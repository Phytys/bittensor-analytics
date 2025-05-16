import bittensor as bt
import sys
import getpass
from pathlib import Path
import os
import platform
import shutil

def get_bittensor_home() -> Path:
    """Get the Bittensor home directory, respecting BITTENSOR_HOME env var."""
    return Path(os.getenv('BITTENSOR_HOME', Path.home() / '.bittensor'))

def get_save_location():
    """Get and display the save location information."""
    backup_dir = get_bittensor_home() / 'wallet_backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Detect OS and show relevant path
    is_windows = platform.system() == 'Windows'
    if is_windows:
        # Convert to Windows-style path for WSL
        linux_str = str(backup_dir)
        windows_str = f"\\\\wsl$\\Ubuntu-22.04{linux_str}"
        print("\n=== Save Location Information (Windows) ===")
        print(f"Windows path: {windows_str}")
    else:
        path = str(backup_dir)
        print("\n=== Save Location Information (Linux/WSL) ===")
        print(f"Linux path: {path}")
        print("\nTo view the backup file:")
        print(f"  cd {path}")
        print("  ls -la  # to see hidden files")
    
    print("\n⚠️  SECURITY RECOMMENDATIONS:")
    print("1. Move backup files to an encrypted drive")
    print("2. Use full-disk encryption (LUKS/BitLocker)")
    print("3. Consider GPG-encrypting the backup file")
    print("4. Never leave mnemonics on an unencrypted drive")
    print("===============================\n")
    return backup_dir

def get_network_choice():
    """Get and validate network choice from user."""
    print("\n=== Network Selection ===")
    print("IMPORTANT: Choose your network carefully!")
    print("\nTESTNET:")
    print("✓ Uses test tokens (tTAO) with no real value")
    print("✓ Perfect for learning and testing")
    print("✓ All features available (subnets, staking, etc.)")
    print("✓ Can get free test tokens from faucets")
    print("❌ Cannot be used on mainnet")
    print("\nMAINNET:")
    print("✓ Uses real TAO tokens with real value")
    print("✓ For actual production/staking")
    print("✓ All features available")
    print("❌ Real financial risk")
    print("❌ Cannot be used on testnet")
    print("===============================\n")

    while True:
        choice = input("Enter network choice (test/main): ").strip().lower()
        if choice in ['test', 'main']:
            # Require explicit confirmation for mainnet
            if choice == 'main':
                print("\n⚠️  WARNING: You are creating a MAINNET wallet!")
                print("This will use real TAO tokens with real value.")
                confirm = input("Type 'YES' to confirm mainnet wallet creation: ").strip().upper()
                if confirm != 'YES':
                    print("Mainnet wallet creation cancelled.")
                    continue
            return choice
        print("❌ Invalid choice. Please enter 'test' or 'main'")

def check_existing_wallet(wallet_name: str, network: str, backup_dir: Path) -> bool:
    """Check if wallet already exists in keystore or backup."""
    # Check backup file
    backup_file = backup_dir / f'{wallet_name}_{network}_mnemonics.txt'
    if backup_file.exists():
        print(f"\n⚠️  WARNING: A wallet backup already exists at:")
        print(f"   {backup_file}")
        return True

    # Check keystore using BITTENSOR_HOME
    keystore_path = get_bittensor_home() / 'wallets' / wallet_name
    if keystore_path.exists():
        print(f"\n⚠️  WARNING: A wallet with name '{wallet_name}' already exists in keystore!")
        print(f"   Location: {keystore_path}")
        return True

    return False

def save_mnemonics(cold_mnemonic: str, hot_mnemonic: str, wallet_name: str, network: str, backup_dir: Path) -> Path:
    """Save both coldkey and hotkey mnemonics to a file in a secure location."""
    backup_file = backup_dir / f'{wallet_name}_{network}_mnemonics.txt'
    temp_file = backup_dir / f'{wallet_name}_{network}_mnemonics.txt.tmp'
    is_encrypted = False
    
    try:
        # Write to temporary file first
        with open(temp_file, 'w') as f:
            f.write(f"Network: {network.upper()}NET\n")
            f.write(f"Wallet Name: {wallet_name}\n")
            f.write(f"\n=== Coldkey Mnemonic (24 words) ===\n")
            f.write(f"{cold_mnemonic}\n")
            f.write(f"\n=== Hotkey Mnemonic (24 words) ===\n")
            f.write(f"{hot_mnemonic}\n")
            f.write("\nIMPORTANT: Keep these mnemonics secure and preferably offline.\n")
            f.write("Anyone with these mnemonics can access your wallet and tokens.\n")
            if network == 'main':
                f.write("\n⚠️  MAINNET WALLET - REAL TAO TOKENS ⚠️\n")
            else:
                f.write("\n⚠️  TESTNET WALLET - TEST TOKENS ONLY ⚠️\n")
            f.write(f"\nSave Location:\n")
            f.write(f"Path: {backup_file}\n")
            f.write("\nTo verify wallet after creation:\n")
            f.write(f"btcli wallet inspect --wallet.name {wallet_name}\n")
            f.write("\nTo recreate this wallet if needed:\n")
            f.write(f"btcli wallet regen_coldkey --mnemonic \"{cold_mnemonic}\"\n")
            f.write(f"btcli wallet regen_hotkey --mnemonic \"{hot_mnemonic}\"\n")
        
        # Set secure permissions before moving to final location
        temp_file.chmod(0o600)  # Owner read/write only
        
        # Move temp file to final location
        shutil.move(temp_file, backup_file)
        
        print(f"\n✅ Mnemonics saved to: {backup_file}")
        print("\n⚠️  IMPORTANT: This backup file is currently in plain text!")
        print("You have two options to secure it:")
        print("1. Move it to a secure offline location (recommended)")
        print("2. Encrypt it with GPG")
        
        # Ask if user wants to encrypt the backup file
        encrypt_choice = input("\nWould you like to encrypt the backup file with GPG? (y/N): ").strip().lower()
        if encrypt_choice == 'y':
            try:
                # Check if GPG is installed
                if shutil.which('gpg') is None:
                    print("\n❌ GPG is not installed. Please install it first:")
                    print("  sudo apt-get install gnupg")
                else:
                    print("\nEncrypting backup file with GPG...")
                    # Prompt for passphrase twice
                    while True:
                        passphrase1 = getpass.getpass("Enter a passphrase to encrypt the backup file: ")
                        passphrase2 = getpass.getpass("Retype the passphrase: ")
                        if passphrase1 != passphrase2:
                            print("❌ Passphrases do not match. Please try again.")
                        elif len(passphrase1) < 8:
                            print("❌ Passphrase should be at least 8 characters. Please try again.")
                        else:
                            break
                    print("⚠️  Remember this passphrase - you'll need it to decrypt the file!")
                    encrypted_file = backup_file.with_suffix('.txt.gpg')
                    # Use symmetric encryption with a passphrase in batch mode
                    # --batch --yes disables interactive prompt, --pinentry-mode loopback allows passphrase from stdin
                    gpg_cmd = f"gpg --batch --yes --symmetric --armor --output {encrypted_file} --passphrase '{passphrase1}' --pinentry-mode loopback {backup_file}"
                    result = os.system(gpg_cmd)
                    # Clear passphrase from memory
                    passphrase1 = passphrase2 = None
                    if encrypted_file.exists() and result == 0:
                        backup_file.unlink()
                        print(f"\n✅ Encrypted backup saved to: {encrypted_file}")
                        print("\nTo decrypt this file later:")
                        print(f"1. Run: gpg --decrypt {encrypted_file}")
                        print("2. Enter the passphrase you just set")
                        print("\nOr save to a file:")
                        print(f"gpg --decrypt --output decrypted_mnemonics.txt {encrypted_file}")
                        backup_file = encrypted_file
                        is_encrypted = True
                    else:
                        print("❌ Failed to encrypt the backup file")
            except Exception as e:
                print(f"❌ Error encrypting file: {str(e)}")
        
        return backup_file, is_encrypted
        
    except Exception as e:
        # Clean up temp file if it exists
        if temp_file.exists():
            temp_file.unlink()
        raise e

def create_new_wallet():
    print("\n=== Bittensor Wallet Creation ===")
    print("This script will help you create a new Bittensor wallet.")
    print("You will need to:")
    print("1. Choose a network (testnet or mainnet)")
    print("2. Choose a wallet name")
    print("3. Set a secure password")
    print("4. Save the mnemonic phrases")
    print("\nIMPORTANT: Running this script multiple times with the same wallet name")
    print("will create a new wallet each time and overwrite the previous backup!")
    print("===============================\n")

    backup_file = None
    try:
        # Get and display save location first
        backup_dir = get_save_location()
        
        # Get network choice
        network = get_network_choice()
        
        # Get wallet name from user
        wallet_name = input("\nEnter a name for your wallet (e.g., 'my_wallet'): ").strip()
        if not wallet_name:
            raise ValueError("Wallet name cannot be empty")
        
        # Check for existing wallet
        if check_existing_wallet(wallet_name, network, backup_dir):
            print("\nThis means either:")
            print("1. You already created this wallet before")
            print("2. Someone else created a wallet with this name")
            print("\nIf you continue, you will:")
            print("✓ Create a new wallet with the same name")
            print("✓ Overwrite the existing backup file")
            print("❌ NOT be able to access the old wallet if you don't have its mnemonics")
            
            confirm = input("\nType 'YES' to create a new wallet (this will overwrite the old backup): ").strip().upper()
            if confirm != 'YES':
                print("Wallet creation cancelled.")
                sys.exit(0)
        
        # Set hotkey name
        hotkey_name = f"{wallet_name}_hotkey"

        # Initialize connection to the network
        print(f"\nConnecting to {network.upper()}NET...")
        try:
            # Simple connection with just network parameter
            sub = bt.Subtensor(network=network)
            print(f"✅ Connected to {network.upper()}NET successfully")
            print(f"Network: {network.upper()}NET")
        except Exception as e:
            print(f"\n❌ Failed to connect to {network.upper()}NET: {str(e)}")
            print("\nPossible solutions:")
            print("1. Check your internet connection")
            print("2. Try again in a few minutes")
            print("3. If the problem persists, try using a different network")
            print("4. You can also try using the CLI command:")
            print(f"   btcli wallet new --wallet.name {wallet_name} --wallet.hotkey {hotkey_name}")
            sys.exit(1)

        # Create wallet object
        print(f"\nCreating {network.upper()}NET wallet '{wallet_name}'...")
        wallet = bt.wallet(name=wallet_name, hotkey=hotkey_name)
        
        # Generate new coldkey and hotkey (24 words each)
        print("\n=== Creating Coldkey (Main Wallet Key) ===")
        print("This key controls your tokens and is used for important operations.")
        print("\nYou will now be asked to set a wallet encryption password.")
        print("This password is used to encrypt your coldkey on your computer.")
        print("⚠️  This is DIFFERENT from the backup file - it only encrypts the wallet key!")
        print("⚠️  Remember this password - it cannot be recovered if lost!")
        print("⚠️  You will need this password every time you use your wallet!")
        print("===============================")
        print("\nGenerating new coldkey (24 words)...")
        
        # Create new coldkey and capture its mnemonic
        coldkey = wallet.create_new_coldkey(n_words=24)
        print("\n=== IMPORTANT: Coldkey Mnemonic ===")
        print("The mnemonic above is your coldkey backup phrase.")
        print("Please copy it EXACTLY as shown and paste it below.")
        print("This will be used to create your backup file.")
        print("===============================")
        while True:
            cold_mnemonic = input("\nPaste the coldkey mnemonic (24 words): ").strip()
            if len(cold_mnemonic.split()) != 24:
                print("❌ Error: The mnemonic must be exactly 24 words. Please try again.")
                continue
            break
        
        print("\n=== Creating Hotkey (Operational Key) ===")
        print("This key is used for day-to-day operations like staking.")
        print("\nYou will now be asked to set a different wallet encryption password.")
        print("This password is used to encrypt your hotkey on your computer.")
        print("⚠️  This is DIFFERENT from the backup file - it only encrypts the wallet key!")
        print("⚠️  Remember this password - it cannot be recovered if lost!")
        print("⚠️  You will need this password for operations like staking!")
        print("===============================")
        print("Generating new hotkey (24 words)...")
        
        # Create new hotkey and capture its mnemonic
        hotkey = wallet.create_new_hotkey(n_words=24)
        print("\n=== IMPORTANT: Hotkey Mnemonic ===")
        print("The mnemonic above is your hotkey backup phrase.")
        print("Please copy it EXACTLY as shown and paste it below.")
        print("This will be used to create your backup file.")
        print("===============================")
        while True:
            hot_mnemonic = input("\nPaste the hotkey mnemonic (24 words): ").strip()
            if len(hot_mnemonic.split()) != 24:
                print("❌ Error: The mnemonic must be exactly 24 words. Please try again.")
                continue
            break

        # Save both mnemonics
        backup_file, is_encrypted = save_mnemonics(cold_mnemonic, hot_mnemonic, wallet_name, network, backup_dir)
        
        print("\n=== Wallet Created Successfully ===")
        print(f"Network: {network.upper()}NET")
        print(f"Wallet Name: {wallet_name}")
        print(f"Coldkey SS58: {wallet.coldkeypub.ss58_address}")
        print(f"Hotkey SS58:  {wallet.hotkey.ss58_address}")
        print("\n=== Important Information ===")
        print(f"1. This is a {network.upper()}NET wallet")
        if network == 'main':
            print("   ⚠️  Uses real TAO tokens with real value!")
        else:
            print("   ℹ️  Uses test tokens (tTAO) with no real value")
        print("2. Your mnemonics have been saved to:")
        print(f"   {backup_file}")
        if is_encrypted:
            print("   ✅ Backup file is encrypted with GPG")
            print("   ℹ️  Use 'gpg --decrypt' to view the contents")
        else:
            print("   ⚠️  Backup file is in plain text!")
            print("   ℹ️  Consider encrypting it with GPG or moving to a secure location")
        print("3. You have set two encryption passwords:")
        print("   - Coldkey password: Protects your main wallet key")
        print("   - Hotkey password: Protects your operational key")
        print("   ⚠️  Both passwords cannot be recovered if lost!")
        print("4. Keep your mnemonics secure and offline")
        print("5. Verify your wallet with:")
        print(f"   btcli wallet inspect --wallet.name {wallet_name}")
        print("6. You can recreate this wallet using the mnemonics with:")
        print(f"   btcli wallet regen_coldkey --mnemonic \"{cold_mnemonic}\"")
        print(f"   btcli wallet regen_hotkey --mnemonic \"{hot_mnemonic}\"")
        print("===============================")

    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}", file=sys.stderr)
        # Clean up backup file if it was created
        if backup_file and backup_file.exists():
            backup_file.unlink()
        sys.exit(1)

if __name__ == "__main__":
    create_new_wallet() 