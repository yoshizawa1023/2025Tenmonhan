# ライブラリのインポート
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from analyze import spectrum, drawGraph, removeBaselines
import sqlite3
import math

from dopler_tracking import calculate_velocity_correction

# 定数の定義
Redius = 8.15
Step=0.1
Earth_position = 8.15
weight = 1000
N=30

C=299792.458 # 光速 [km/s]
f=1420.40575177 # 水素線の周波数 [MHz]

# 銀河系の回転速度
v= 236 # km/s

delta_theta=25 #指向性


# 視線速度の計算(シミュレーション)
x,y=np.meshgrid(np.arange(-Redius-3,Redius+3,Step),np.arange(-Earth_position,Redius+3,Step))
x,y=x.flatten(),y.flatten()
theta = np.arctan(-x/(Redius+y))
r=np.sqrt(x**2+y**2)

v_r=v*(Earth_position/np.sqrt(x**2+y**2)-1)*(-x)/np.sqrt((Earth_position+y)**2+x**2)
v_r=np.where((x**2+y**2>1),v_r,0)

# データベースからデータを取得する部分

# データベースに接続
conn = sqlite3.connect('merged_observation_log_for_mitsudo.db')

# クエリの実行
query = """
    SELECT id,galactic_longitude,observed_at,spectrum_data
    FROM observations
    WHERE galactic_latitude = 0 AND peak IS NOT NULL AND peak != ''
"""
df = pd.read_sql_query(query, conn)

# 接続を閉じる
conn.close()

galaxy_data = np.zeros_like(x)
couter = np.zeros_like(x)

# 行を一つずつ処理していく
for index, row in df.iterrows():
    # 各行のデータを取得
    #データの整形
    spectrum_array = removeBaselines(np.array(eval(row['spectrum_data'])))
    spectrum_pd = pd.DataFrame(spectrum_array.T, columns=['frequency', 'intensity'])
    spectrum_pd['v_r'] = C*(f-spectrum_pd['frequency'])/f
    spectrum_pd['v_lsr']= spectrum_pd['v_r']   # LSR速度の計算
    # フィルター類の計算
    # 視線速度の計算
    filter_of_angle=np.logical_and(theta>np.deg2rad(row['galactic_longitude']-delta_theta),theta<np.deg2rad(row['galactic_longitude']+delta_theta))

    # データを帯に分けて，色塗りをする。
    min=spectrum_pd['v_lsr'].min()
    max=spectrum_pd['v_lsr'].max()

    #minからmaxまでをn個に分割した配列
    kukan,n_kukan = np.linspace(min, max, N, retstep=True,endpoint=False)
    kukan = np.append(kukan, max)
    width_kukan = kukan[1]-kukan[0]

    for i in range(N):
        filter_of_speed = np.logical_and(v_r > kukan[i], v_r < kukan[i+1])

        sum_of_intensity = sum(spectrum_pd[np.logical_and(spectrum_pd['v_lsr']>=kukan[i],spectrum_pd['v_lsr']<kukan[i+1])]['intensity'])*weight
        filter_kukan = np.where(np.logical_and(filter_of_speed,filter_of_angle), 1, 0)
        num_of_points = sum(filter_kukan)
        
        # どっちかがゼロ以下ならスキップ
        if (num_of_points == 0 or sum_of_intensity <= 0):
            continue

        galaxy_data[np.where(np.logical_and(filter_of_speed,filter_of_angle))] += sum_of_intensity/ num_of_points
        couter[np.where(np.logical_and(filter_of_speed,filter_of_angle))] += 1
    
# ゼロで割ってしまうことをふせぐために、カウンターがゼロのところはカウンターに1を代入
couter[couter == 0] = 1
# 平均を計算
result = galaxy_data / couter
#result[result==0]=9999
# 結果の可視化
plt.figure(figsize=(10, 10))
plt.scatter(x, y, c=result, s=1, cmap="jet")
plt.gca().set_aspect('equal')
plt.colorbar(label='Intensity')
plt.clim(0,0.8)
# galactic_plane_observation.csvを読み込んで一緒にプロット
galactic_df = pd.read_csv('galactic_plane_observation.csv')
plt.scatter(galactic_df['x'], galactic_df['y']-Earth_position, c='red', s=1, label='Galactic Plane Observations')
plt.gca().set_aspect('equal')
plt.scatter([0], [-Earth_position], marker="o", color="red", label="Earth Position")
plt.scatter([0], [0], marker="o", color="blue", label="Galaxy Center")

plt.show()