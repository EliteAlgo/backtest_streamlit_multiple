import re
import json
import os
from collections import defaultdict

def analyze_backtest(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract JSON using regex
    match = re.search(r'let \$_json = (\[.*?\]);', content, re.DOTALL)
    if not match:
        print("Could not find $_json variable in the file.")
        return

    json_str = match.group(1)
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return

    total_days = len(data)
    total_pnl = 0
    win_days = 0
    loss_days = 0
    max_profit_day = {'date': '', 'pnl': -float('inf')}
    max_loss_day = {'date': '', 'pnl': float('inf')}
    total_trades = 0
    
    print(f"{'Date':<15} | {'Daily PNL':>12} | {'Sum PNL':>12} | {'Trades':>6} | {'Result':<4}")
import re
import json
import os
from collections import defaultdict

def analyze_backtest(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract JSON using regex
    match = re.search(r'let \$_json = (\[.*?\]);', content, re.DOTALL)
    if not match:
        print("Could not find $_json variable in the file.")
        return

    json_str = match.group(1)
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return

    total_days = len(data)
    total_pnl = 0
    win_days = 0
    loss_days = 0
    max_profit_day = {'date': '', 'pnl': -float('inf')}
    max_loss_day = {'date': '', 'pnl': float('inf')}
    total_trades = 0
    
    print(f"{'Date':<15} | {'Daily PNL':>12} | {'Sum PNL':>12} | {'Trades':>6} | {'Result':<4}")
    print("-" * 65)

    total_legs = 0
    total_winning_trades = 0
    total_losing_trades = 0
    
    # Strategy stats aggregation by day
    # Structure: strategy_daily_pnl[strategy][date] = daily_sum
    strategy_daily_pnl = defaultdict(lambda: defaultdict(float))

    for day_data in data:
        date = day_data.get('RD', 'Unknown')
        daily_pnl = day_data.get('DP', 0)
        
        trades = day_data.get('LR', [])
        num_trades = len(trades) # This is number of setups
        
        sum_pnl = 0
        
        for trade_setup in trades:
            # Each item in LR is a strategy setup/execution
            strategy_name = trade_setup.get('ON', 'Unknown')
            setup_pnl = trade_setup.get('PNL', 0)
            sum_pnl += setup_pnl
            
            group_key = strategy_name[:5]
            
            # Aggregate PNL by day for this strategy
            strategy_daily_pnl[group_key][date] += setup_pnl
            
            # Count trades within this setup
            legs = trade_setup.get('LD', [])
            num_legs = len(legs)
            total_legs += num_legs
            
            # Count individual leg wins/losses for the total stats
            for leg in legs:
                leg_pnl = leg.get('PNL', 0)
                if leg_pnl > 0:
                    total_winning_trades += 1
                elif leg_pnl < 0:
                    total_losing_trades += 1
        
        # Use DP as the official PNL for now, but show sum_pnl too
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

        print(f"{date:<15} | {daily_pnl:>12.2f} | {sum_pnl:>12.2f} | {num_trades:>6} | {result:<4}")

    print("-" * 65)
    print(f"Total Days: {total_days}")
    print(f"Total PNL: {total_pnl:.2f}")
    print(f"Total Trades: {total_trades}")
    print(f"Win Days: {win_days}")
    print(f"Loss Days: {loss_days}")
    print(f"Win Rate (Days): {win_days / total_days * 100:.2f}%" if total_days > 0 else "Win Rate (Days): N/A")
    print(f"Trade Win Rate: {total_winning_trades / total_legs * 100:.2f}% ({total_winning_trades}W / {total_losing_trades}L)" if total_legs > 0 else "Trade Win Rate: N/A")
    print(f"Max Profit Day: {max_profit_day['date']} ({max_profit_day['pnl']:.2f})")
    print(f"Max Loss Day: {max_loss_day['date']} ({max_loss_day['pnl']:.2f})")
    print(f"Avg PNL per Day: {total_pnl / total_days:.2f}" if total_days > 0 else "Avg PNL: N/A")
    
    print("\nStrategy Analysis (Grouped by first 5 chars) - Daily Stats")
    print(f"{'Strategy':<10} | {'Total PNL':>12} | {'Days':>6} | {'Win Rate':>10} | {'Avg Daily':>10}")
    print("-" * 60)
    
    for strategy, daily_data in strategy_daily_pnl.items():
        total_strat_pnl = sum(daily_data.values())
        days_traded = len(daily_data)
        winning_days = sum(1 for pnl in daily_data.values() if pnl > 0)
        
        win_rate = (winning_days / days_traded * 100) if days_traded > 0 else 0
        avg_daily_pnl = total_strat_pnl / days_traded if days_traded > 0 else 0
        
        print(f"{strategy:<10} | {total_strat_pnl:>12.2f} | {days_traded:>6} | {win_rate:>9.2f}% | {avg_daily_pnl:>10.2f}")

if __name__ == "__main__":
    file_path = r"c:\Users\Admin\OneDrive\Desktop\code\backtest\a.htm"
    analyze_backtest(file_path)
