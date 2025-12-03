import re
import json
from collections import defaultdict
import pandas as pd

# Copied from app.py to verify logic in isolation
def parse_backtest_data(content):
    match = re.search(r'let \$_json = (\[.*?\]);', content, re.DOTALL)
    if not match:
        return None
    
    json_str = match.group(1)
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError:
        return None

def analyze_data(data):
    total_days = len(data)
    total_pnl = 0
    win_days = 0
    loss_days = 0
    max_profit_day = {'date': '', 'pnl': -float('inf')}
    max_loss_day = {'date': '', 'pnl': float('inf')}
    total_trades = 0
    
    # Strategy stats aggregation by day and execution
    strategy_daily_pnl = defaultdict(lambda: defaultdict(float))
    strategy_exec_stats = defaultdict(lambda: {'max_profit': [], 'max_drawdown': [], 'vix': [], 'sl_hits': 0, 'total_execs': 0})

    daily_summary_data = []

    for day_data in data:
        date = day_data.get('RD', 'Unknown')
        daily_pnl = day_data.get('DP', 0)
        
        trades = day_data.get('LR', [])
        num_trades = len(trades)
        
        sum_pnl = 0
        
        for trade_setup in trades:
            strategy_name = trade_setup.get('ON', 'Unknown')
            setup_pnl = trade_setup.get('PNL', 0)
            sum_pnl += setup_pnl
            
            group_key = strategy_name[:5]
            
            # Aggregate PNL by day for this strategy
            strategy_daily_pnl[group_key][date] += setup_pnl
            
            # Collect execution stats
            stats = strategy_exec_stats[group_key]
            stats['total_execs'] += 1
            stats['max_profit'].append(trade_setup.get('_max', 0))
            stats['max_drawdown'].append(trade_setup.get('_min', 0))
            stats['vix'].append(trade_setup.get('VST', 0))
            
            legs = trade_setup.get('LD', [])
            sl_hit = False
            for leg in legs:
                # The fix is here:
                if 'OnSL' in (leg.get('Er') or ''):
                    sl_hit = True
                    break
            if sl_hit:
                stats['sl_hits'] += 1
        
        pnl = daily_pnl
        total_pnl += pnl
        total_trades += num_trades
        
        if pnl > 0:
            win_days += 1
            result = "WIN"
        elif pnl < 0:
            loss_days += 1
            result = "LOSS"
        else:
            result = "BREAK"

        if pnl > max_profit_day['pnl']:
            max_profit_day = {'date': date, 'pnl': pnl}
        
        if pnl < max_loss_day['pnl']:
            max_loss_day = {'date': date, 'pnl': pnl}
            
        daily_summary_data.append({
            "Date": date,
            "Daily PNL": daily_pnl,
            "Sum PNL": sum_pnl,
            "Trades": num_trades,
            "Result": result
        })

    return "Success"

try:
    with open('a.htm', 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = parse_backtest_data(content)
    if data:
        print("Data parsed successfully.")
        result = analyze_data(data)
        print(result)
    else:
        print("Failed to parse data.")

except Exception as e:
    print(f"Error: {e}")
