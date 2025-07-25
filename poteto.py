import discord
from discord.ext import commands, tasks
import os
from keep_alive import keep_alive
from flask import Flask, request
from datetime import timedelta
import requests
import json
import asyncio
import random
from pydub import AudioSegment

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

app = Flask(__name__)
keep_alive()

bot = commands.Bot(command_prefix='!', intents=intents)
client = discord.Client(intents = intents)
CHANNEL_ID = 927549442465349632

# PERSPECTIVE_API
PERSPECTIVE_API_KEY = "AIzaSyD6yd1tmX9S7QtkJTeJyn7rqe1UaiCtno4"
# 許容できる不適切スコアの閾値
TOXICITY_THRESHOLD = 0.3
# 監視対象のユーザーID
TARGET_USER_IDS = {449487835351744515}

# ポテトのユーザーID
POTATO_ID = 449487835351744515

#テスト用チャンネル(テキスト)のID
TEST_CHANNEL_ID = 1349011383882223667

# ループ用のチャンネルを動的に格納
loop_target_channel = None

# 文字列の危険度判定
async def analyze_text(text):
    
    """Perspective API"""
    url = f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={PERSPECTIVE_API_KEY}"
    data = {
        "comment": {"text": text},
        "languages": ["ja"],  
        "requestedAttributes": {"TOXICITY": {}}
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, data=json.dumps(data), headers=headers)
    
    
    if response.status_code == 200:
        result = response.json()
        toxicity_score = result["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
        return toxicity_score
    else:
        print(f"Perspective API エラー: {response.status_code}, {response.text}")
        return None


# メッセージ受信時に動作する処理
@bot.event
async def on_message(message):
    
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return

    
    target_user = message.guild.get_member(POTATO_ID)  # 指定されたユーザーを取得(ポテト)
    mentioned_user = message.mentions  # メンションされたユーザー(1人目)を取得
    
    #　リスト入りしているユーザーによりボットがメンションされた場合
    if message.author.id in TARGET_USER_IDS:

        #危険度を測定
        toxicity_score = await analyze_text(message.content)
        # 危険性が規定値以上に認められた場合
        if toxicity_score is not None and toxicity_score > TOXICITY_THRESHOLD:
            # タイムアウト（mute）処理
            min = 10  # 10分タイムアウト
            await target_user.timeout(timedelta(minutes=min), reason="ホモのためタイムアウト(危険度)")
            await message.channel.send(f"{target_user} の発言は不適切と判断したため、ファックします。{min}分間ミュートされます。危険度 = {toxicity_score}")

    #　その他ユーザーによりボットがメンションされた場合
    elif bot.user in message.mentions:
        # ユーザーが存在する場合
        if target_user:  
            #ポテトファッカーを実行
            await potato_fucker(message,target_user)
            
        else:
            await print("user=none")

    # 動作後、コマンド処理を続ける
    await bot.process_commands(message)



async def potato_fucker(message, target_user):
    # タイムアウト処理
        try:
            content_without_mentions = message.content
            for mention in message.mentions:
                # メンション部分以外のテキストを取得
                content_without_mentions = int(content_without_mentions.replace(mention.mention, ""))

            if content_without_mentions == "解除":
                await target_user.timeout(None)
            # メンション以外のテキストがint型に変換できる場合
            elif isinstance(content_without_mentions, int):
                min = content_without_mentions / 60
                
                # 指定時間タイムアウト
                await target_user.timeout(timedelta(minutes=min), reason="ホモのためタイムアウト(時間指定)")
                await message.channel.send(f"Potato was fucked! ({min}min) ")
            else:
                await target_user.timeout(timedelta(minutes=0.1), reason="ホモのためタイムアウト(デフォルト)")
                await message.channel.send("Potato was fucked!")
        except:
            #例外時、再度ポテトファックを試行
            #ここで例外が発生した場合はキャッチしない
            await target_user.timeout(timedelta(minutes=0.1), reason="ホモのためタイムアウト(例外)")
            await message.channel.send("Potato was fucked!")



@tasks.loop(seconds=10)
async def timeout_loop():
    for guild in bot.guilds:
        member = guild.get_member(POTATO_ID)
        if member:
            # 100%の確率でタイムアウト
            if random.random() < 0.1:
                try:
                    # タイムアウト期間
                    until = discord.utils.utcnow() + timedelta(seconds=5)
                    await member.timeout(until, reason="ランダムタイムアウト")
                    await loop_target_channel.send("自走ファックを行います。(10秒毎,1/10)")
                except Exception as e:
                    print(f"タイムアウト失敗: {e}")

@bot.command()
async def enable(ctx):
    """タイムアウト処理開始"""
    if not timeout_loop.is_running():
        loop_target_channel = ctx.channel
        timeout_loop.start()
        await ctx.send("自走式ポテトファッカーを起動します。")


@bot.command()
@commands.has_role("G") 
async def disable(ctx):
    """タイムアウト処理停止"""
    if timeout_loop.is_running():
        timeout_loop.stop()
        await ctx.send("自走式ポテトファッカーを停止します。")


# @bot.command()
# async def start_record(ctx:discord.ApplicationContext):

#         # コマンドを使用したユーザーのボイスチャンネルに接続
#         try:
#             vc = await ctx.author.voice.channel.connect()
#             await ctx.respond("録音開始...")
#         except AttributeError:
#             await ctx.respond("ボイスチャンネルに入ってください。")
#             return
        
#         # 録音開始。mp3で帰ってくる。wavだとなぜか壊れる。
#         ctx.voice_client.start_recording(discord.sinks.MP3Sink(), finished_callback, ctx)

# @bot.command()
# async def stop_recording(ctx:discord.ApplicationContext):
#         # 録音停止
#         ctx.voice_client.stop_recording() 
#         await ctx.respond("録音終了!")
#         await ctx.voice_client.disconnect()

# # 録音終了時に呼び出される関数
# async def finished_callback(sink:discord.sinks.MP3Sink, ctx:discord.ApplicationContext):
#     print("test")
    # 録音したユーザーの音声を取り出す
    # for user_id, audio in sink.audio_data.items():
    #     # mp3ファイルとして書き込み。その後wavファイルに変換。
    #     song = AudioSegment.from_file(audio.file, format="mp3")
    #     song.export(f"./{user_id}.wav", format='wav')



#以下編集しないこと
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
