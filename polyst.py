import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import time

# ==========================================
# 🌐 模組: Live Web Scraper (即時爬蟲)
# ==========================================
class RotowireScraper:
    """
    專門用於抓取 Rotowire 的 NBA 與 NHL 每日陣容與傷病資訊。
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.urls = {
            "NBA": "https://www.rotowire.com/basketball/nba-lineups.php",
            "NHL": "https://www.rotowire.com/hockey/nhl-lineups.php"
        }

    def fetch_injuries(self, league="NBA"):
        """
        訪問 Rotowire 並返回 {球隊: [傷病名單]} 字典
        """
        url = self.urls.get(league.upper())
        if not url:
            print(f"❌ Error: League {league} not supported.")
            return {}

        print(f"📡 Connecting to Rotowire {league} Lineups...")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Connection failed: Status {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            lineup_boxes = soup.find_all("div", class_="lineup__box")
            
            injury_report = {}
            
            for box in lineup_boxes:
                # 抓取對戰雙方球隊代碼 (e.g., LAL, BOS)
                # Rotowire 的 HTML 結構通常在 lineup__top 或 lineup__teams 中
                # 這裡使用簡單的 text search 或 class 查找
                teams = []
                team_divs = box.find_all("a", class_="lineup__team") # 常見結構
                if not team_divs: # Fallback
                     team_divs = box.find_all("div", class_="lineup__team-abbr")
                
                for t in team_divs:
                    teams.append(t.text.strip())
                
                # 抓取該區塊內的傷病資訊
                # Rotowire 通常將傷病放在 class="lineup__injured" 或帶有 "OUT", "GTD" 的標籤中
                # 為了通用性，我們抓取所有帶有 "is-injured" 或 "is-gtd" class 的球員
                
                # 分離主客隊有點複雜，這裡我們簡化為：抓取該比賽所有缺陣球員，並嘗試歸屬
                # 簡單策略：將整個 box 的傷兵列出，實戰中通常我們看球員名字就知道是哪隊
                
                injured_players = []
                # 查找所有標註為 OUT 或 GTD 的標籤
                for status_tag in box.find_all("span", class_=["lineup__injuries-status", "lineup__status"]):
                    status_text = status_tag.text.strip().upper()
                    if status_text in ["OUT", "GTD", "DOUBTFUL"]:
                        # 找到對應的球員名字 (通常是 status 的父級或兄弟級元素)
                        player_node = status_tag.find_parent("li") or status_tag.find_parent("div")
                        if player_node:
                            player_name = player_node.find("a").text.strip() if player_node.find("a") else "Unknown"
                            injured_players.append(f"{player_name} ({status_text})")
                
                # 將傷病資訊綁定到這場比賽的球隊
                matchup_key = f"{teams[0]} vs {teams[1]}" if len(teams) >= 2 else "Unknown Matchup"
                if injured_players:
                    injury_report[matchup_key] = injured_players
                    
            print(f"✅ Scraped {len(lineup_boxes)} games. Found injuries in {len(injury_report)} matchups.")
            return injury_report

        except Exception as e:
            print(f"❌ Scraping Error: {e}")
            return {}

# ==========================================
# 🚀 System Identity: The Edge v2.4 (Integrated)
# ==========================================
class TheEdgeSystem:
    def __init__(self, csv_path="nba_2026_totals.csv"):
        self.csv_path = csv_path
        self.data_2026 = None
        self.scraper = RotowireScraper() # 載入爬蟲模組
        self.live_injuries = {}          # 儲存即時抓取的傷病
        
        # 載入 2026 模擬數據
        self._load_csv_data()

    def _load_csv_data(self):
        try:
            df = pd.read_csv(self.csv_path)
            # 簡單計算 EFF/36
            df = df.fillna(0)
            df['EFF'] = (df['PTS'] + df['TRB'] + df['AST'] + df['STL'] + df['BLK'] - 
                         (df['FGA'] - df['FG']) - (df['FTA'] - df['FT']) - df['TOV'])
            df['EFF_per_36'] = np.where(df['MP'] > 50, df['EFF'] / df['MP'] * 36, 0)
            self.data_2026 = df
        except:
            print("⚠️ CSV not found. Running in Web-Only Mode.")
            self.data_2026 = pd.DataFrame()

    def scan_live_web(self, league="NBA"):
        """
        執行指令: Scan 2025 (實時模式)
        """
        print(f"\n🌐 --- [LIVE WEB SCAN] Protocol Initiated: {league} ---")
        
        # 1. 執行爬蟲
        self.live_injuries = self.scraper.fetch_injuries(league)
        
        if not self.live_injuries:
            print("⚠️ No games found or scraping blocked. Check internet connection.")
            return

        # 2. 顯示並分析
        print("\n📋 Rotowire Live Injury Report:")
        for matchup, players in self.live_injuries.items():
            print(f"⚔️  {matchup}")
            for p in players:
                print(f"   🚨 {p}")
                
        print("\n💡 Alpha Analysis based on Live Data:")
        for matchup, players in self.live_injuries.items():
            # 簡單關鍵字觸發邏輯
            if any("OUT" in p for p in players):
                print(f"👉 **Sniper Alert**: Significant absence in {matchup}. Check odds movement.")

# ==========================================
# 🎮 使用者操作區
# ==========================================
if __name__ == "__main__":
    edge = TheEdgeSystem()
    
    # 指令: 掃描 NBA 即時傷病
    # 這會實際訪問 https://www.rotowire.com/basketball/nba-lineups.php
    edge.scan_live_web(league="NBA")
    
    # 指令: 掃描 NHL 即時傷病
    # 這會實際訪問 https://www.rotowire.com/hockey/nhl-lineups.php
    print("\n-------------------\n")
    edge.scan_live_web(league="NHL")