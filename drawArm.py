import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from dopler_tracking import calculate_velocity_correction
import japanize_matplotlib # 追加

def get_observation_data():
    """
    observation_log_mukai.dbから観測データをDataFrameとして取得します。
    galactic_latitude=0で、peakが空でないデータのみを対象とします。
    """
    # データベースに接続
    conn = sqlite3.connect('merged_observation_log_arm.db')
    
    # クエリの実行
    query = """
        SELECT galactic_longitude, ra, dec, peak, observed_at
        FROM observations
        WHERE galactic_latitude = 0 AND peak IS NOT NULL AND peak != ''
    """
    df = pd.read_sql_query(query, conn)
    
    # 接続を閉じる
    conn.close()
    
    return df

def process_data(df):
    """
    取得したデータをプロット用に処理します。
    この関数はユーザーが自由に定義できるように、編集用のスペースを設けています。

    引数:
        df (pd.DataFrame): 観測データ。'galactic_longitude', 'ra', 'dec', 'peak' カラムを持つ。

    戻り値:
        tuple: x, y のタプル
    """
    # ===============================================================
    # ここから下を編集して、xとyの値を計算してください。
    # df (Pandas DataFrame) の列: ['galactic_longitude', 'ra', 'dec', 'peak']

    # 'peak'列の文字列 '[1111,2222]' をリストに変換
    # 安全でない可能性があるため、信頼できるデータソースでのみevalを使用してください

    # 定数
    R_0 = 8.15  # 太陽から銀河中心までの距離 (kpc)
    V_0 = 236  # 太陽の銀河系内の公転速度 (km/s)
    c=299792.458  # 光速 (km/s)
    f_0 = 1420.40575177  # 水素線の周波数 (MHz)

    df['peak'] = df['peak'].apply(eval)

    # 各peak値に対して行を複製
    df = df.explode('peak')
    df['v_lsr']=c*(f_0-df['peak']) / f_0  # v_lsr = c * peak / f_0
    # 補正量を計算
    df['v_correction'] = df.apply(lambda row: calculate_velocity_correction(row['observed_at'], row['galactic_longitude'], 0), axis=1)
    # 補正後の速度を計算
    df['v_corrected'] = df['v_lsr'] #- df['v_correction']
    df['R']=R_0*V_0*np.sin(np.radians(df['galactic_longitude'])) / (V_0*np.sin(np.radians(df['galactic_longitude'])) + df['v_corrected'])
    
    
    # df['R']**2- R_0**2 * np.sin(np.radians(df['galactic_longitude']))が負になる場合は削除
    df=df[df['R']**2- R_0**2 * np.sin(np.radians(df['galactic_longitude']))>=0]
    df['r']=(df['R']**2- R_0**2 * np.sin(np.radians(df['galactic_longitude']))**2)**0.5+R_0**np.cos(np.radians(df['galactic_longitude']))
    # xとyの値を設定
    x = df['r']*-np.sin(np.radians(df['galactic_longitude']))
    y = df['r']*np.cos(np.radians(df['galactic_longitude']))
    df['x'] = x
    df['y'] = y
    # csvファイルに保存
    df.to_csv('galactic_plane_observation.csv', index=False)
    # ===============================================================

    return x, y

def main():
    """
    メインの処理
    """
    # データの取得
    observation_df = get_observation_data()
    
    if observation_df.empty:
        print("対象のデータが見つかりませんでした。")
        return

    # データの処理
    x, y = process_data(observation_df)

    # グラフの描画
    plt.scatter(x, y, marker='o', label='ピークから読み取った点')
    plt.xlabel("横方向 (kpc)", fontsize=14)
    plt.ylabel("奥行き方向 (kpc)", fontsize=14)
    plt.title("観測から得た銀河系の概形",fontsize=16)
    plt.scatter([0], [0], marker="o", color="red", label="太陽の位置")
    plt.scatter([0], [8.15], marker="o", color="blue", label="銀河中心の位置")
    plt.xlim(-10, 10)
    plt.grid(True)
    # 縦横比を1:1に設定
    plt.axis('equal')
    #字を大きく
    plt.tick_params(labelsize=14)
    

    plt.legend()
    plt.show()

if __name__ == "__main__":
    main()
