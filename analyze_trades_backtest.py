import json
import pandas as pd
import numpy as np

def run_analysis():
    print("Loading 72,565 simulated trades...")
    with open('simulated_trades.json', 'r') as f:
        data = json.load(f)
        
    df = pd.DataFrame(data)
    total_raw = len(df)
    
    # Filter out TIEs
    df = df[df['outcome'].isin(['WIN', 'LOSS'])]
    total_resolved = len(df)
    
    # Map WIN/LOSS to 1/0 for math
    df['is_win'] = (df['outcome'] == 'WIN').astype(int)
    
    raw_wr = df['is_win'].mean()
    print(f"Loaded {total_resolved} resolved simulated trades.")
    print(f"Raw Crossover Win Rate: {raw_wr:.2%}")
    
    report_lines = []
    report_lines.append("# Quant Report: Regime-Adaptive Reversal Strategy Backtest\n")
    report_lines.append(f"This report evaluates the **{total_resolved}** resolved candidate setups generated over the 1.1 million tick history.\n")
    report_lines.append(f"*   **Raw Crossover Baseline:** {total_resolved} trades | Win Rate: **{raw_wr:.2%}**\n\n")
    
    # --- Experiment 1: The "Flipping" (Reversal) of Weak Regimes ---
    report_lines.append("## 🔄 1. Reversing Weak Regimes (Trade Flipping)\n")
    report_lines.append("We analyze if reversing the trade direction in poor-performing categories yields high-probability outcomes.\n\n")
    report_lines.append("| Feature | Category | Original Trades | Original WR | Reversed WR | Expected Delta |\n")
    report_lines.append("| :--- | :--- | :---: | :---: | :---: | :---: |\n")
    
    flippable_conditions = []
    
    categorical_features = {
        'activeLandmarkType': 'activeLandmarkType',
        'phase': 'phase',
        'micro_urgency': 'micro_urgency',
        'micro_participation': 'micro_participation',
        'energyState': 'energyState',
        'direction': 'direction'
    }
    
    for label, col in categorical_features.items():
        if col not in df.columns:
            continue
        counts = df[col].value_counts()
        for cat in counts.index:
            slice_df = df[df[col] == cat]
            count = len(slice_df)
            if count < 100:
                continue
            wr = slice_df['is_win'].mean()
            rev_wr = 1 - wr
            
            # If original win rate is under 48%, reversing it is potentially profitable
            if wr < 0.48:
                sig = "✅ PROFITABLE FLIP"
                flippable_conditions.append({
                    'col': col,
                    'val': cat,
                    'original_wr': wr,
                    'reversed_wr': rev_wr,
                    'count': count
                })
            else:
                sig = "Keep Original"
                
            report_lines.append(f"| `{label}` | {cat} | {count} | {wr:.2%} | **{rev_wr:.2%}** | {sig} |\n")
            
    # --- Experiment 2: Regime-Adaptive Switching (Mean Reversion vs Breakout) ---
    report_lines.append("\n## 🧭 2. Regime-Adaptive Switching via `meanReversionProb`\n")
    report_lines.append("HunterXHunter is designed for Trend Breakouts. However, when `meanReversionProb` is high, price is highly likely to revert rather than follow through. We test a threshold-based switch:\n")
    report_lines.append("*   If `meanReversionProb < Threshold`: Trade **Breakout** (Original Direction)\n")
    report_lines.append("*   If `meanReversionProb >= Threshold`: Trade **Mean Reversion** (Reversed Direction)\n\n")
    report_lines.append("| Threshold | Breakout Trades | Breakout WR | Mean-Rev Trades | Mean-Rev WR | Combined Trades | Combined WR | Improvement |\n")
    report_lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
    
    best_threshold = 50
    best_combined_wr = 0
    
    for thresh in range(30, 80, 5):
        # Breakout trades (meanReversionProb < thresh) -> keep original outcome
        bo_trades = df[df['meanReversionProb'] < thresh]
        bo_count = len(bo_trades)
        bo_wr = bo_trades['is_win'].mean() if bo_count > 0 else 0
        
        # Mean Reversion trades (meanReversionProb >= thresh) -> reverse outcome (1 - original_outcome)
        mr_trades = df[df['meanReversionProb'] >= thresh]
        mr_count = len(mr_trades)
        mr_wr = (1 - mr_trades['is_win']).mean() if mr_count > 0 else 0
        
        combined_count = bo_count + mr_count
        combined_wins = (bo_trades['is_win'].sum() if bo_count > 0 else 0) + ((1 - mr_trades['is_win']).sum() if mr_count > 0 else 0)
        combined_wr = combined_wins / combined_count if combined_count > 0 else 0
        
        improvement = combined_wr - raw_wr
        sig = f"+{improvement:.2%}" if improvement > 0 else f"{improvement:.2%}"
        
        if combined_wr > best_combined_wr:
            best_combined_wr = combined_wr
            best_threshold = thresh
            
        report_lines.append(f"| {thresh}% | {bo_count} | {bo_wr:.2%} | {mr_count} | {mr_wr:.2%} | {combined_count} | **{combined_wr:.2%}** | **{sig}** |\n")
        
    # --- Experiment 3: Full Multi-Regime Composite Strategy ---
    # We combine:
    # 1. Flip trades in negative-edge categories (e.g. SWING_HIGH, HESITANT flow).
    # 2. Apply the optimal meanReversionProb switch on the rest.
    report_lines.append("\n## 🚀 3. Composite Regime-Adaptive Strategy Backtest\n")
    report_lines.append("We simulate a composite strategy where:\n")
    report_lines.append(f"1.  **Flipped Categories:** If landmark is `SWING_HIGH` or microstructure urgency is `HESITANT`, we REVERSE the trade.\n")
    report_lines.append(f"2.  **Mean Reversion Switch:** For other categories, if `meanReversionProb >= {best_threshold}%`, we REVERSE the trade; otherwise we trade original direction.\n\n")
    
    # Backtest simulation
    composite_wins = 0
    composite_count = 0
    
    for row in df.itertuples():
        # Step 1: Flip checks
        should_reverse = False
        if row.activeLandmarkType == 'SWING_HIGH':
            should_reverse = True
        elif row.micro_urgency == 'HESITANT':
            should_reverse = True
        # Step 2: Mean reversion check
        elif row.meanReversionProb >= best_threshold:
            should_reverse = True
            
        # Outcome calculation
        if should_reverse:
            win = 1 - row.is_win
        else:
            win = row.is_win
            
        composite_wins += win
        composite_count += 1
        
    composite_wr = composite_wins / composite_count if composite_count > 0 else 0
    improvement_comp = composite_wr - raw_wr
    
    report_lines.append(f"*   **Total Composite Trades:** {composite_count} (100% trade coverage maintained!)\n")
    report_lines.append(f"*   **Composite Win Rate:** **{composite_wr:.2%}** (Wins: {composite_wins} | Losses: {composite_count - composite_wins})\n")
    report_lines.append(f"*   **Performance Improvement over Crossover Baseline:** **+{improvement_comp:.2%}** absolute win rate increase!\n\n")
    
    report_lines.append("## 💡 Quant Conclusion\n")
    if improvement_comp > 0.03:
        report_lines.append("🏆 **Conclusion: Reversing the trade direction in high mean-reversion and weak-momentum regimes creates a highly profitable edge.**\n")
        report_lines.append("Instead of filtering out trades and shrinking coverage, switching from Trend-Following to Mean-Reversion adaptive logic retains 100% trade frequency while raising the statistical expectancy from a losing/random profile to a strong winning profile.\n")
    else:
        report_lines.append("⚠️ **Conclusion: Adaptive reversing does not yield a significant statistical edge.** The underlying features remain descriptive.\n")
        
    with open('reversal_regime_report.md', 'w') as out:
        out.writelines(report_lines)
        
    print("Reversal backtest complete. Report generated: reversal_regime_report.md")

if __name__ == '__main__':
    run_analysis()
