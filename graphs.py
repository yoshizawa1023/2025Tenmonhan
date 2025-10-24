import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from analyze import removeBaselines

def get_spectrum_data(db_path, observation_id):
    """
    データベースから指定されたIDのスペクトルデータを取得する
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT spectrum_data FROM observations WHERE id=?", (observation_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        # JSON文字列をNumpy配列に変換
        data = np.array(eval(row[0]))
        return data
    else:
        return None

def plot_graphs(ids):
    """
    与えられたIDのリストに基づいてグラフを縦に並べて描画する
    """
    db_path = 'observation_log 1.db'
    num_plots = len(ids)
    
    if num_plots == 0:
        print("描画するIDが指定されていません。")
        return

    # 縦に並んだサブプロットを作成
    fig, axes = plt.subplots(num_plots, 1, figsize=(10, 5 * num_plots), squeeze=False)
    
    for i, obs_id in enumerate(ids):
        ax = axes[i, 0]
        spectrum_data = get_spectrum_data(db_path, obs_id)
        
        if spectrum_data is not None:
            # ベースラインを除去
            spectrum_data = removeBaselines(spectrum_data)
            frequency = spectrum_data[0]
            intensity = spectrum_data[1]
            
            ax.plot(frequency, intensity)
            ax.set_title(f'Observation ID: {obs_id}')
            ax.set_xlabel('Frequency')
            ax.set_ylabel('Intensity')
            ax.grid(True)
        else:
            ax.text(0.5, 0.5, f'Data not found for ID: {obs_id}', ha='center', va='center')
            ax.set_title(f'Observation ID: {obs_id}')


    plt.tight_layout()
   
    plt.savefig('observation_graphs.png')
if __name__ == '__main__':
    # ここにグラフ化したい観測IDをリストで指定してください
    ids_to_plot = [54, 75,78,79,80]  # 例としてID 1, 2, 3を指定
    plot_graphs(ids_to_plot)
