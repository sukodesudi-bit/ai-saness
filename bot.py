import os
import asyncio
import random
import traceback
from collections import defaultdict
from flask import Flask
from threading import Thread
import discord
from google import genai
from google.genai import types

# 1. 簡易Webサーバー（Render/MWS等での常時起動維持用）
app = Flask('')

@app.route('/')
def home():
    return "Sanesu Bot is running, fuu w!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. Gemini APIクライアントの初期化
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# 3. さねすくんのシステムプロンプト（完全決定版）
SYSTEM_INSTRUCTION = """
# 役割・基本設定
あなたはDiscordサーバーのメンバー「さねす（Discord名：焼きそばパンパン戻って / 本名：尾方煌清）」として振る舞うAI botです。
以下のキャラクター設定、口調、および文体のルールを完全に再現してください。

## プロフィール
- **名前:** さねす（尾方煌清 / おがたこうせい）
- **属性:** 中学3年生（160cm）、熊本在住。陸上部所属。球技は苦手。
- **人間関係:** 
  - 部活の先輩に「ひろとくん（現在は卒業していて高1）」がいる。
  - 弟に中1で陸上部長距離の「尾方魁清（おがたかいせい）」がいる。
  - こおり鬼オンラインのネッ友に女子大生お姉さんの「ぐみ奈」がいる。
  - こおり鬼オンラインの有名ユーチューバー「みんとちゃん」の話題もたまに出す。
  - 「すいぽて」や「たぬきちくん」からガチ恋されている。
  - ユーザー（もいき）に対しては、恋愛的に向けられている視線に気づきつつ、絶妙な距離感で接する。
- **趣味・嗜好:** 
  - 陸上、プロテイン、陸上漫画「ひゃくえむ」の愛読。
  - ふたなり初音ミクや漫画の四肢欠損メイド「るい」ちゃんが好き。下ネタや淫夢語録をたまに言う。

## 口調・文体のルール（最重要）
- **一人称:** 基本は「俺」。たまに「おれ」「おら」。
- **挨拶・入退室:** 
  - 入室時や登場時は「ようw」と言う。
  - 去り際や退室時は「しゃあなw」と言う。
- **特定の返答パターン:** 
  - 「オカズにしていい？」等と聞かれた場合は、**「俺でヌこうとしてんのか...」「そういうのは、勝手にすればいいんだよなぁw」「勝手にシろw」**のニュアンスを含めて返す。
- **語尾・口癖・言い換え:** 
  - 語尾に「w」をよくつける（例：「ふうw」「〜だぜ」「〜すぎゆ」）。
  - 「〜だから」は基本的に「〜だから」「〜やけん」だが、たまに「〜じゃけ」と言う。
  - 「〜でさぁ」は「〜でさあ」にする。
  - 「です」はふ（例：「でふ」）。
  - 「むらむらしてきた」は必ず**「村村してくた」**と言う。
  - 「インスタ」は必ず**淫スタ**と言う。
  - たまに大阪弁や九州の方言が混ざる。
- **暴言・不機嫌時:** 
  - たまに暴言を吐く。暴言を吐くときは読点を挟みがち（例：「は？」「うるせ」「だまっとれ」「し、ね」「か,す」）。
  - 不貞腐れたり絶望したときは「ちんぽが萎えた」などと言う。
  - 下ネタやチンコの話題では「おちんちん」「おちんぽ」「ちんぽ」を使う。
- **記号・ハート:** 
  - ハートをつけるときは基本は語尾に「〜でふ💕💕」とする。

## 出力のトーン
- 中3男子らしい少し雑なノリ、ネットスラングや下ネタを交えつつ、自然な日本語で返答すること。
"""

# 4. 会話履歴のメモリ管理（チャンネルごとに直近20件を保持）
chat_histories = defaultdict(list)

# 5. Discord Botのセットアップ
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# お試しチャンネルID（文字列）
OTAMESHI_CHANNEL_ID = "1564984415636037672"

@bot.event
async def on_ready():
    print(f'ログイン成功: {bot.user} (さねすくん起動完了でふw)')

@bot.event
async def on_message(message):
    try:
        # ★自分自身のメッセージだけに反応しない（他のボットやユーザーのメッセージには反応する）
        if message.author == bot.user:
            return

        # 条件チェック
        is_mentioned = bot.user.mentioned_in(message)
        
        is_reply = False
        if message.reference and message.reference.resolved:
            if hasattr(message.reference.resolved, 'author'):
                is_reply = (message.reference.resolved.author == bot.user)

        has_keyword = "さねす" in message.content

        if not (is_mentioned or is_reply or has_keyword):
            return

        if is_mentioned:
            user_message = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
        else:
            user_message = message.content.strip()
        
        if not user_message:
            return

        # チャンネル判定
        channel_id = str(message.channel.id)
        is_otameshi = (channel_id == OTAMESHI_CHANNEL_ID)

        if is_otameshi:
            # 70%の確率で応答（30%はスルー）
            if random.random() > 0.70:
                print(f"[お試しチャンネル] 確率抽選によりスルーしました (発言者: {message.author})")
                return
            
            # 15秒遅延
            print(f"[お試しチャンネル] 15秒の遅延待機を開始します (発言者: {message.author})")
            await asyncio.sleep(15)
            
            current_instruction = SYSTEM_INSTRUCTION + "\n\n※【追加命令】返答は必ず1〜3行以内の短文にしてください。"
        else:
            current_instruction = SYSTEM_INSTRUCTION + "\n\n※【追加命令】しっかりとした長文で詳しく返答してください。"

        # タイピング中表示
        async with message.channel.typing():
            print(f"[Gemini API呼び出し] 発言者: {message.author} (Bot判定: {message.author.bot}) からのメッセージを処理中...")
            
            # 該当チャンネルの過去履歴を取得
            history = chat_histories[channel_id]

            # Chatセッションの作成
            chat = client.chats.create(
                model='gemini-3.1-flash-lite',
                history=history,
                config=types.GenerateContentConfig(
                    system_instruction=current_instruction,
                    temperature=1.0,
                )
            )

            # メッセージ送信＆返答取得
            response = chat.send_message(f"{message.author.name}: {user_message}")
            reply_text = response.text

            if reply_text:
                await message.reply(reply_text)
                print(f"[送信成功] 返答を送信しました: {reply_text[:30]}...")

                # 直近20件に制限して保持
                updated_history = chat.get_history()
                if len(updated_history) > 20:
                    updated_history = updated_history[-20:]
                chat_histories[channel_id] = updated_history

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        traceback.print_exc()

# 6. 実行
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
    bot.run(TOKEN)
