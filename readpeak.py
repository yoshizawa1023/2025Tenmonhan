
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import json
from analyze import removeBaselines

class PeakSelector:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.check_and_add_peak_column()

        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT id, spectrum_data FROM observations ORDER BY id")
        self.rows = self.cursor.fetchall()
        self.current_index = 0
        self.peaks = []

        if not self.rows:
            print("観測データがありません。")
            self.conn.close()
            return

        self.fig, self.ax = plt.subplots()
        plt.subplots_adjust(bottom=0.2)

        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        
        ax_next = plt.axes([0.81, 0.05, 0.1, 0.075])
        self.btn_next = Button(ax_next, 'next')
        self.btn_next.on_clicked(self.next_data)

        self.plot_data()
        plt.show()

    def check_and_add_peak_column(self):
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(observations)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'peak' not in columns:
            print("カラム 'peak' が存在しないため、追加します。")
            cursor.execute("ALTER TABLE observations ADD COLUMN peak TEXT")
            self.conn.commit()

    def plot_data(self):
        if self.current_index >= len(self.rows):
            print("All data has been processed.")
            plt.close(self.fig)
            self.conn.close()
            return

        self.ax.clear()
        self.peaks = []
        
        obs_id, spectrum_data_json = self.rows[self.current_index]
        data = np.array(eval(spectrum_data_json))
        data_baseline_removed = removeBaselines(data)
        self.ax.plot(data_baseline_removed[0], data_baseline_removed[1])
        self.ax.set_title(f"Observation ID: {obs_id}")
        self.ax.set_xlabel("frequency (MHz)")
        self.ax.set_ylabel("intensity")
        self.ax.grid(True)
        self.fig.canvas.draw()

    def onclick(self, event):
        if event.inaxes != self.ax:
            return
        
        x_val = event.xdata
        self.peaks.append(x_val)
        
        self.ax.plot(x_val, event.ydata, 'rx', markersize=10)
        print(f"記録された周波数: {x_val:.4f}")
        self.fig.canvas.draw()

    def next_data(self, event):
        obs_id, _ = self.rows[self.current_index]
        
        # データをDBに保存
        peaks_json = json.dumps(self.peaks)
        self.cursor.execute("UPDATE observations SET peak = ? WHERE id = ?", (peaks_json, obs_id))
        self.conn.commit()
        print(f"ID: {obs_id} peak: {self.peaks} saved to DB.")

        self.current_index += 1
        self.plot_data()

if __name__ == '__main__':
    DB_PATH = 'merged_observation_log.db'
    # データベースファイルの場所を特定するために探す
    # このスクリプトは/Users/naoki/Desktop/rtl-sdr/build/src/にあるので、
    # データベースは/Users/naoki/Desktop/rtl-sdr/build/にあると仮定する
    db_file_path = '/Users/naoki/Desktop/rtl-sdr/build/merged_observation_log.db'
    
    # もし上記パスになければ、カレントディレクトリを探す
    import os
    if not os.path.exists(db_file_path):
        db_file_path = DB_PATH

    PeakSelector(db_file_path)
