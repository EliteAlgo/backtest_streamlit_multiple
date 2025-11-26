import streamlit as st
import pandas as pd
import re
import json
from collections import defaultdict
import io

st.set_page_config(page_title="Backtest Analyzer", layout="wide")

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
                if 'OnSL' in str(leg.get('Er') or ''):
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

    # Strategy Analysis Table
    strategy_data = []
    for strategy, daily_data in strategy_daily_pnl.items():
        total_strat_pnl = sum(daily_data.values())
        days_traded = len(daily_data)
        winning_days = sum(1 for pnl in daily_data.values() if pnl > 0)
        
        win_rate = (winning_days / days_traded * 100) if days_traded > 0 else 0
        avg_daily_pnl = total_strat_pnl / days_traded if days_traded > 0 else 0
        
        daily_pnls = list(daily_data.values())
        max_loss_day_strat = min(daily_pnls) if daily_pnls else 0
        max_profit_day_strat = max(daily_pnls) if daily_pnls else 0
        
        strategy_data.append({
            "Strategy": strategy,
            "Total PNL": total_strat_pnl,
            "Days": days_traded,
            "Win Rate": f"{win_rate:.1f}%",
            "Avg Daily": avg_daily_pnl,
            "Max Loss (Day)": max_loss_day_strat,
            "Max Profit (Day)": max_profit_day_strat
        })

    summary_metrics = {
        "Total Days": total_days,
        "Total PNL": total_pnl,
        "Total Trades": total_trades,
        "Win Days": win_days,
        "Loss Days": loss_days,
        "Win Rate (Days)": f"{win_days / total_days * 100:.2f}%" if total_days > 0 else "N/A",
        "Max Profit Day": f"{max_profit_day['date']} ({max_profit_day['pnl']:.2f})",
        "Max Loss Day": f"{max_loss_day['date']} ({max_loss_day['pnl']:.2f})",
        "Avg PNL per Day": total_pnl / total_days if total_days > 0 else 0
    }

    return pd.DataFrame(daily_summary_data), pd.DataFrame(strategy_data), summary_metrics

st.title("📊 Backtest Report Analyzer")

uploaded_file = st.file_uploader("Upload your backtest report (HTML file)", type=["htm", "html"])

if uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8")
    data = parse_backtest_data(content)
    
    if data:
        daily_df, strategy_df, metrics = analyze_data(data)
        
        st.header("Summary Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total PNL", f"{metrics['Total PNL']:.2f}")
        col2.metric("Win Rate (Days)", metrics['Win Rate (Days)'])
        col3.metric("Total Days", metrics['Total Days'])
        col4.metric("Avg PNL / Day", f"{metrics['Avg PNL per Day']:.2f}")
        
        st.subheader("Strategy Analysis")
        st.dataframe(strategy_df, use_container_width=True)
        
        st.subheader("Daily Performance")
        st.dataframe(daily_df, use_container_width=True)
        
        # Excel Export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            strategy_df.to_excel(writer, sheet_name='Strategy Analysis', index=False)
            daily_df.to_excel(writer, sheet_name='Daily Summary', index=False)
            pd.DataFrame([metrics]).to_excel(writer, sheet_name='Overall Metrics', index=False)
            
        st.download_button(
            label="📥 Download Analysis as Excel",
            data=output.getvalue(),
            file_name="backtest_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    else:
        st.error("Could not parse the file. Please ensure it's a valid backtest report.")
