from app.fundamentals import fetch_alpha_apy
from app.models import SubnetAPY
from app.scripts.warmup_base import run_warmup

if __name__ == "__main__":
    print("🚀 Starting APY data collection...")
    run_warmup(fetch_fn=fetch_alpha_apy, model_class=SubnetAPY, name="apy", min_age_hours=6)
    print("✨ APY data collection complete!")
