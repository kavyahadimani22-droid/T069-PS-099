import argparse
from pathlib import Path
from src.file_handler import load_market
from src.pricing import price_all_loads
from src.matching import run_matching_cycle
from src.reporting import write_price_report,write_matching_log,write_settlements
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data",default="data");ap.add_argument("--output",default="outputs");a=ap.parse_args()
    m=load_market(a.data);prices=price_all_loads(m);proposals=run_matching_cycle(m,prices)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    write_price_report(prices,out/"price_breakdown.csv");write_matching_log(proposals,out/"matching_log.csv");write_settlements(m.trips,out/"settlement_statements.csv")
    print(f"Loads={len(m.loads)} proposals={len(proposals)}")
if __name__=="__main__":main()
