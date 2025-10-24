import jsonargparse
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import japanize_matplotlib  # 日本語対応のためのインポート
def spectrum(id: int):
    conn = sqlite3.connect('observation_log.db')
    cursor = conn.cursor()
    cursor.execute("SELECT spectrum_data FROM observations WHERE id=?", (id,))
    row = cursor.fetchone()
    conn.close()
    print(row)

def drawGraph(id: int, baseline: bool = False):
    conn = sqlite3.connect('observation_log.db')
    cursor = conn.cursor()
    cursor.execute("SELECT spectrum_data FROM observations WHERE id=?", (id,))
    row = cursor.fetchone()
    conn.close()
    # row[0]:JSONからdata:numpy配列に変換
    data= np.array(eval(row[0]))
    if baseline:
        data = removeBaselines(data)
    # C*(f-spectrum_pd['frequency'])/f
    C = 299792.458  # 光速 [km/s]
    f = 1420.40575177  # 水素線の周波数

    plt.plot(data[0], data[1])
    plt.ylim(-0.005,0.015)
    plt.xlabel('周波数[MHz]',fontsize=14)
    plt.ylabel('強度', fontsize=14)
    # フォントサイズの調整
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.savefig(f'spectrum_{id}.png', dpi=300, bbox_inches='tight')


    # csvファイルに保存
    df = pd.DataFrame(data.T, columns=['frequency', 'intensity'])
    df.to_csv(f'spectrum_{id}.csv', index=False)

def removeBaselines(data: np.ndarray):
    data_panas = pd.DataFrame(data.T, columns=['frequency', 'intensity'])
    # ベースライン処理(改善が必要)
    scoped=data_panas[(data_panas['frequency']>1419.5) & (data_panas['frequency']<1421.25)]
    res=np.polyfit(scoped['frequency'], scoped['intensity'], 2)
    base=np.polyval(res, scoped['frequency'])
    scoped2=scoped[scoped['intensity']<base]
    res2=np.polyfit(scoped2['frequency'], scoped2['intensity'], 2)
    scoped3=scoped[scoped['intensity']<base]
    res3=np.polyfit(scoped3['frequency'], scoped3['intensity'], 2)
    scoped4=scoped[scoped['intensity']<base]
    res4=np.polyfit(scoped4['frequency'], scoped4['intensity'], 2)
    result=scoped.copy()
    result['intensity']=scoped['intensity']-np.polyval(res4, scoped['frequency'])
    #print(result)
    return result.to_numpy().T
if __name__ == "__main__":
    jsonargparse.CLI()