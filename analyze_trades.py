import json
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind

def analyze():
    print("Loading extracted trade features...")
    with open('extracted_trades.json', 'r') as f:
        data = json.load(f)
        
    df = pd.DataFrame(data)
    
    # Filter only resolved trades
    df = df[df['outcome'].isin(['WIN', 'LOSS'])]
    
    total_trades = len(df)
    winners = df[df['outcome'] == 'WIN']
    losers = df[df['outcome'] == 'LOSS']
    
    win_rate = len(winners) / total_trades if total_trades > 0 else 0
    print(f"Total resolved trades in history: {total_trades}")
    print(f"Overall Win Rate: {win_rate:.2%}")
    print(f"Wins: {len(winners)} | Losses: {len(losers)}")
    
    # Identify continuous features
    continuous_features = [
        'persistence', 'velocity', 'volatility', 'slope', 'consistency', 'tapeSpeed',
        'relPos', 'displacement10', 'energy', 'trendQuality', 'commitment', 'noiseLevel',
        'liquidityStability', 'breakoutProb', 'meanReversionProb', 'microstructureHealth',
        'suitabilityScore', 'distLandmark', 'bounceProbability', 'breakoutProbability',
        'levelRespectRate', 'micro_persistence', 'micro_acceleration', 'micro_hesitation',
        'micro_exhaustion', 'micro_randomness', 'lm_momentumHealth', 'lm_directionalEfficiency',
        'lm_pressure', 'lm_acceleration', 'lm_instability', 'lm_randomness', 'mci'
    ]
    
    continuous_results = []
    for feat in continuous_features:
        if feat not in df.columns:
            continue
        
        win_vals = winners[feat].dropna().values
        loss_vals = losers[feat].dropna().values
        
        if len(win_vals) < 2 or len(loss_vals) < 2:
            continue
            
        mean_win = np.mean(win_vals)
        mean_loss = np.mean(loss_vals)
        diff = mean_win - mean_loss
        
        # T-test
        t_stat, p_val = ttest_ind(win_vals, loss_vals, equal_var=False)
        
        continuous_results.append({
            'feature': feat,
            'mean_win': mean_win,
            'mean_loss': mean_loss,
            'diff': diff,
            'p_value': p_val if not np.isnan(p_val) else 1.0,
            't_stat': t_stat if not np.isnan(t_stat) else 0.0
        })
        
    df_cont = pd.DataFrame(continuous_results)
    df_cont['abs_t'] = df_cont['t_stat'].abs()
    df_cont = df_cont.sort_values(by='p_value')
    
    # Identify categorical features
    categorical_features = [
        'direction', 'trend', 'compression', 'exhaustion', 'phase', 'activeLandmarkType',
        'decisionDelay', 'micro_participation', 'micro_urgency', 'energyState'
    ]
    
    categorical_results = {}
    for feat in categorical_features:
        if feat not in df.columns:
            continue
            
        group = df.groupby(feat)['outcome'].value_counts().unstack().fillna(0)
        if 'WIN' not in group.columns:
            group['WIN'] = 0
        if 'LOSS' not in group.columns:
            group['LOSS'] = 0
            
        group['total'] = group['WIN'] + group['LOSS']
        group['win_rate'] = group['WIN'] / group['total']
        group = group.sort_values(by='total', ascending=False)
        categorical_results[feat] = group
        
    # Write the Markdown Report
    with open('trade_analysis_report.md', 'w') as out:
        out.write("# Quantitative Analysis of Trade History: Winning vs. Losing Characteristics\n\n")
        out.write(f"This report evaluates the **{total_trades}** resolved trades to determine what winning and losing setups have in common.\n\n")
        out.write(f"**Baseline Stats:**\n")
        out.write(f"*   Total Trades: {total_trades}\n")
        out.write(f"*   Wins: {len(winners)} ({win_rate:.2%})\n")
        out.write(f"*   Losses: {len(losers)} ({1-win_rate:.2%})\n\n")
        
        out.write("## 📈 1. Continuous Features: Differences in Means\n")
        out.write("Ranked by statistical significance ($p$-value). Low $p$-values ($<0.05$) indicate that the feature is strongly linked to the outcome.\n\n")
        out.write("| Rank | Feature | Winner Mean | Loser Mean | Difference | $p$-value | Significance |\n")
        out.write("| :--- | :--- | :---: | :---: | :---: | :---: | :--- |\n")
        
        for idx, row in enumerate(df_cont.itertuples(), 1):
            sig = "⭐⭐⭐ Very High" if row.p_value < 0.01 else ("⭐⭐ High" if row.p_value < 0.05 else ("⭐ Marginal" if row.p_value < 0.1 else "None"))
            out.write(f"| {idx} | `{row.feature}` | {row.mean_win:.4f} | {row.mean_loss:.4f} | {row.diff:+.4f} | {row.p_value:.4f} | {sig} |\n")
            
        out.write("\n## 📊 2. Categorical Features & Win Rates\n")
        out.write("This section shows the performance of categorical market states.\n\n")
        
        for feat, group in categorical_results.items():
            out.write(f"### Feature: `{feat}`\n")
            out.write("| Category | Wins | Losses | Total Trades | Win Rate |\n")
            out.write("| :--- | :---: | :---: | :---: | :---: |\n")
            for cat, row in group.iterrows():
                out.write(f"| {cat} | {int(row['WIN'])} | {int(row['LOSS'])} | {int(row['total'])} | {row['win_rate']:.2%} |\n")
            out.write("\n")
            
        # Top winning and losing rules
        out.write("## 💡 3. Key Findings & Strategic Insights\n")
        out.write("Based on the data, here are the most significant observations:\n\n")
        
        # Pull out top features
        top_cont = df_cont[df_cont['p_value'] < 0.1].head(3)
        if len(top_cont) > 0:
            out.write("### Significant Continuous Variables:\n")
            for r in top_cont.itertuples():
                direction = "higher" if r.diff > 0 else "lower"
                out.write(f"*   **`{r.feature}`**: Winners have a **{direction}** value ({r.mean_win:.4f}) compared to losers ({r.mean_loss:.4f}) with $p={r.p_value:.4f}$.\n")
        else:
            out.write("*   No continuous variables had high statistical significance ($p < 0.1$), indicating that isolated indicators do not easily separate winners and losers.\n")
            
    print("Analysis complete. Markdown report generated: trade_analysis_report.md")

if __name__ == '__main__':
    analyze()
