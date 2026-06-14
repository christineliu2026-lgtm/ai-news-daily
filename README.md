# 馃實 鍏ㄧ悆 AI 閲嶅ぇ鏂伴椈鏃ユ姤

姣忓ぉ鏃?8:00 鑷姩鎺ㄩ€佹缇?+ 涓浗 AI 绐佺牬鎬ф柊闂诲埌寰俊锛屽畬鍏ㄥ厤璐广€佷簯绔繍琛岋紝鐢佃剳鍏虫満涔熻兘鏀跺埌銆?
## 蹇€熷紑濮嬶紙绾?5 鍒嗛挓锛?
### 绗?1 姝ワ細鑾峰彇 Gemini API Key锛堝厤璐癸級

1. 鎵撳紑 https://aistudio.google.com/apikey
2. 浣跨敤 Google 璐﹀彿鐧诲綍
3. 鐐瑰嚮銆孋reate API Key銆?4. 澶嶅埗鐢熸垚鐨?key锛堟牸寮忓 `AIza...`锛?
> Gemini 鍏嶈垂棰濆害锛氭瘡澶?1500 娆¤姹傦紝瀹屽叏澶熺敤

### 绗?2 姝ワ細鑾峰彇 PushPlus Token锛堝厤璐癸級

1. 鎵撳紑 https://www.pushplus.plus
2. 寰俊鎵爜鐧诲綍
3. 鍦ㄣ€屽彂閫佹秷鎭€嶁啋銆屼竴瀵逛竴娑堟伅銆嶉〉闈?4. 澶嶅埗浣犵殑 Token锛堟牸寮忓 `xxxxx`锛?
> PushPlus 鍏嶈垂棰濆害锛氭瘡澶?200 鏉?
### 绗?3 姝ワ細閰嶇疆 GitHub

1. Fork 鎴栨帹閫佸埌浣犵殑 GitHub 浠撳簱
2. 杩涘叆 Settings 鈫?Secrets and variables 鈫?Actions
3. 娣诲姞浠ヤ笅 2 涓?Secrets锛?
| Secret Name | 鍐呭 |
|-------------|------|
| `GEMINI_API_KEY` | 绗?1 姝ヨ幏鍙栫殑 Gemini Key |
| `PUSHPLUS_TOKEN` | 绗?2 姝ヨ幏鍙栫殑 PushPlus Token |

### 绗?4 姝ワ細娴嬭瘯

1. 杩涘叆 Actions 鈫?AI News Daily
2. 鐐瑰嚮銆孯un workflow銆嶁啋銆孯un workflow銆?3. 绛?1-2 鍒嗛挓锛屾鏌ュ井淇℃槸鍚︽敹鍒版棩鎶?
### 鍙€夛細NewsAPI Key

濡傞渶鏇村鏂伴椈婧愶紝娉ㄥ唽 https://newsapi.org 鑾峰彇鍏嶈垂 API Key锛?00 娆?澶╋級锛屾坊鍔犱负 `NEWS_API_KEY` Secret銆?
## 宸ヤ綔鍘熺悊

```
GitHub Actions 姣忓ぉ 8:00 瑙﹀彂
    鈫?Python 鑴氭湰鎶撳彇 RSS / NewsAPI 鏂伴椈
    鈫?Gemini AI 绛涢€?+ 涓枃鎬荤粨
    鈫?PushPlus 鎺ㄩ€佸埌寰俊
```

## 瀹氬埗

淇敼 `main.py` 涓殑 `RSS_SOURCES_EN` 鍜?`RSS_SOURCES_CN` 鍙嚜瀹氫箟鏂伴椈婧愩€?