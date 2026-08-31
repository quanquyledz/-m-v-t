import asyncio
import json
import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()  # Đọc biến môi trường từ file .env

logging.basicConfig(
    filename="bot.log",
    level=logging.ERROR,
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

intents = discord.Intents.default()
intents.message_content = True

class DuckBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        GUILD_ID = discord.Object(id=1533999536908009562) 
        self.tree.copy_global_to(guild=GUILD_ID)
        await self.tree.sync(guild=GUILD_ID)
        print("✅ Đã đồng bộ lệnh Slash trực tiếp vào Server!")

bot = DuckBot()

TARGET_CHANNEL_ID = 1543799842017517791 


DATA_FILE = "data.json"
count = 0
last_user_id = None
total_errors = 0
message_lock = asyncio.Lock() 

def load_data():
    global count, last_user_id, total_errors
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                count = data.get("count", 0)
                last_user_id = data.get("last_user_id", None)
                total_errors = data.get("total_errors", 0)
                print(f"📂 Đã tải dữ liệu thành công! (Số vịt: {count}, Lỗi: {total_errors}/5)")
        except Exception as e:
            print(f"⚠️ Không thể đọc file {DATA_FILE}: {e}")
    else:
        save_data()

def save_data():
    data = {
        "count": count,
        "last_user_id": last_user_id,
        "total_errors": total_errors
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"⚠️ Lỗi khi lưu file {DATA_FILE}: {e}")

load_data()

NUMBER_TO_TEXT = {
    1: "một", 2: "hai", 3: "ba", 4: "bốn", 5: "năm",
    6: "sáu", 7: "bảy", 8: "tám", 9: "chín", 10: "mười",
    11: "mười một", 12: "mười hai", 13: "mười ba", 14: "mười bốn", 15: "mười lăm",
    16: "mười sáu", 17: "mười bảy", 18: "mười tám", 19: "mười chín", 20: "hai mươi"
}

TEXT_TO_NUMBER = {
    "một": 1, "mot": 1, "hai": 2, "ba": 3, "bốn": 4, "bon": 4, "năm": 5, "nam": 5,
    "sáu": 6, "sau": 6, "bảy": 7, "bay": 7, "tám": 8, "tam": 8, "chín": 9, "chin": 9, "mười": 10, "muoi": 10
}

def num_to_vietnamese_text(n):
    if n in NUMBER_TO_TEXT:
        return NUMBER_TO_TEXT[n]
    
    units = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    if n < 100:
        ten = n // 10
        unit = n % 10
        ten_str = "mười" if ten == 1 else f"{units[ten]} mươi"
        if unit == 0: return ten_str
        elif unit == 1 and ten > 1: return f"{ten_str} mốt"
        elif unit == 5: return f"{ten_str} lăm"
        elif unit == 4 and ten > 1: return f"{ten_str} tư"
        else: return f"{ten_str} {units[unit]}"
    return str(n)

def extract_first_number_word(content):
    tokens = content.strip().split()
    if not tokens:
        return None, None
    
    first_word = tokens[0]
    first_two_words = " ".join(tokens[:2]) if len(tokens) >= 2 else first_word
    
    return first_word, first_two_words

@bot.event
async def on_ready():
    print(f'🦆 Bot Đếm Vịt ({bot.user}) đã sẵn sàng hoạt động!')
    await bot.change_presence(activity=discord.Game(name="Đếm vịt bằng CHỮ 📝 | Gõ /vit-help"))

@bot.tree.command(name="vit-help", description="Bảng hướng dẫn luật chơi đếm vịt bằng CHỮ")
async def vit_help(interaction: discord.Interaction):
    if interaction.channel_id != TARGET_CHANNEL_ID:
        target_channel = bot.get_channel(TARGET_CHANNEL_ID)
        channel_mention = target_channel.mention if target_channel else "kênh được quy định"
        await interaction.response.send_message(f"⚠️ Bot chỉ hoạt động tại kênh {channel_mention}!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🦆 BẢNG HƯỚNG DẪN GAME ĐẾM VỊT BẰNG CHỮ 📝",
        description="Chào mừng bạn đến với phiên bản Đếm Vịt Bằng Chữ!",
        color=discord.Color.gold()
    )
    embed.add_field(
        name="🎮 LUẬT CHƠI (ĐẾM BẰNG CHỮ):",
        value=(
            "• **Cách đếm:** Nhắn bằng **CHỮ** ở **ĐẦU TỪ** (Ví dụ: `một`, `hai`, `ba`... hoặc `một con vịt`...)\n"
            "• **⚠️ Lỗi đếm bằng chữ số:** Gõ chữ số ở đầu câu (`1`, `2`, `3`...) sẽ bị tính 1 lỗi.\n"
            "• **⚠️ Lỗi đếm sai thứ tự:** Gõ sai chữ số tiếp theo sẽ bị tính 1 lỗi.\n"
            "• **🛑 Giới hạn 5 lỗi:** Tổng số lần vi phạm toàn server chạm mốc **> 5 lần** sẽ bị **Reset về 0**!\n"
            "• **Trò chuyện thoải mái:** Nhắn câu không phải từ đếm ở đầu (Ví dụ: `abc một`) bot sẽ bỏ qua."
        ),
        inline=False
    )
    embed.add_field(
        name="⚡ CÁC LỆNH SLASH (Gõ /):",
        value="• `/vit-help` : Xem bảng hướng dẫn này\n• `/vit-count` : Xem số vịt hiện tại\n• `/vit-reset` : Đặt lại số vịt về 0",
        inline=False
    )
    embed.add_field(
        name="💬 CÁC LỆNH CHAT THƯỜNG (Gõ !):",
        value="• `!duck` hoặc `!vit` : Xem số lượng vịt hiện tại\n• `!resetduck` : Reset game về lại 0",
        inline=False
    )
    embed.set_footer(text="Gõ chữ cẩn thận để đàn vịt không bị bay nhé 🦆📝💨")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="vit-count", description="Xem số lượng vịt hiện tại")
async def vit_count(interaction: discord.Interaction):
    if interaction.channel_id != TARGET_CHANNEL_ID:
        target_channel = bot.get_channel(TARGET_CHANNEL_ID)
        channel_mention = target_channel.mention if target_channel else "kênh được quy định"
        await interaction.response.send_message(f"⚠️ Bot chỉ hoạt động tại kênh {channel_mention}!", ephemeral=True)
        return

    text_val = num_to_vietnamese_text(count) if count > 0 else "không"
    await interaction.response.send_message(f"📊 Đàn vịt hiện tại đang có **{count}** con (**{text_val}** con vịt)! (Tổng lỗi: {total_errors}/5) 🦆")

@bot.tree.command(name="vit-reset", description="Reset game đếm vịt về lại 0")
async def vit_reset(interaction: discord.Interaction):
    if interaction.channel_id != TARGET_CHANNEL_ID:
        target_channel = bot.get_channel(TARGET_CHANNEL_ID)
        channel_mention = target_channel.mention if target_channel else "kênh được quy định"
        await interaction.response.send_message(f"⚠️ Bot chỉ hoạt động tại kênh {channel_mention}!", ephemeral=True)
        return

    global count, last_user_id, total_errors
    count = 0
    last_user_id = None
    total_errors = 0
    save_data()
    await interaction.response.send_message("🔄 Đã reset đàn vịt về **0 (không con vịt)**! Hãy bắt đầu lại bằng: `một` 🦆")

@bot.event
async def on_message(message):
    global count, last_user_id, total_errors

    if message.author == bot.user or message.channel.id != TARGET_CHANNEL_ID:
        return

    content = message.content.strip().lower()
    if not content:
        return

    if content in ['!duck', '!vit']:
        text_val = num_to_vietnamese_text(count) if count > 0 else "không"
        await message.channel.send(f"📊 Đàn vịt hiện tại đang có **{count}** con (**{text_val}** con vịt)! (Tổng lỗi: {total_errors}/5) 🦆")
        return

    if content == '!resetduck':
        count = 0
        last_user_id = None
        total_errors = 0
        save_data()  
        await message.channel.send("🔄 Đã reset đàn vịt về **0**! Hãy bắt đầu lại bằng: `một` 🦆")
        return

    async with message_lock:
        user_id = message.author.id
        expected_next = count + 1
        expected_text = num_to_vietnamese_text(expected_next)

        if content[0].isdigit():
            total_errors += 1
            if total_errors > 5:
                await message.add_reaction('❌')
                embed = discord.Embed(
                    title="💥 TỔNG VI PHẠM QUÁ 5 LẦN: GAME BỊ RESET VỀ 0!",
                    description=f"Mọi người đã vi phạm tổng cộng **{total_errors} lần**! Đàn vịt bị giật mình bay mất rồi! 🦆💨",
                    color=discord.Color.red()
                )
                count = 0
                last_user_id = None
                total_errors = 0
                save_data() 
                await message.channel.send(embed=embed)
            else:
                save_data() 
                await message.add_reaction('⚠️')
                embed = discord.Embed(
                    title=f"⚠️ CẢNH BÁO VI PHẠM! (Tổng lỗi kênh: {total_errors}/5)",
                    description=f"{message.author.mention}, bạn đã gõ chữ số ở đầu câu! Game chỉ chấp nhận đếm bằng **CHỮ**.",
                    color=discord.Color.orange()
                )
                embed.add_field(name="📝 CÁCH ĐẾM ĐÚNG tiếp theo:", value=f"Nhập chữ: **`{expected_text}`** hoặc **`{expected_text} con vịt`**.", inline=False)
                embed.set_footer(text="⚠️ Nếu tổng lỗi toàn server > 5 lần, đàn vịt sẽ bị Reset về 0!")
                await message.channel.send(embed=embed)
            return

        first_word, first_two_words = extract_first_number_word(content)

        is_counting_attempt = False
        attempted_num = None

        if first_two_words == expected_text or first_word == expected_text:
            is_counting_attempt = True
            attempted_num = expected_next
        elif first_word in TEXT_TO_NUMBER:
            is_counting_attempt = True
            attempted_num = TEXT_TO_NUMBER[first_word]

        if not is_counting_attempt:
            await bot.process_commands(message)
            return

        if attempted_num == count:
            await bot.process_commands(message)
            return

        if user_id == last_user_id:
            total_errors += 1
            if total_errors > 5:
                await message.add_reaction('❌')
                embed = discord.Embed(
                    title="💥 TỔNG VI PHẠM QUÁ 5 LẦN: GAME BỊ RESET VỀ 0!",
                    description=f"Mọi người đã vi phạm tổng cộng **{total_errors} lần**! Đàn vịt bị giật mình bay mất rồi! 🦆💨",
                    color=discord.Color.red()
                )
                count = 0
                last_user_id = None
                total_errors = 0
                save_data() 
                await message.channel.send(embed=embed)
            else:
                save_data()
                await message.add_reaction('⚠️')
                await message.channel.send(
                    f'⚠️ {message.author.mention} không được đếm 2 lần liên tiếp! '
                    f'*(Tổng lỗi kênh: {total_errors}/5)*'
                )
            return


        if attempted_num != expected_next:
            total_errors += 1
            if total_errors > 5:
                await message.add_reaction('❌')
                embed = discord.Embed(
                    title="💥 TỔNG VI PHẠM QUÁ 5 LẦN: GAME BỊ RESET VỀ 0!",
                    description=f"Mọi người đã vi phạm tổng cộng **{total_errors} lần**! Đàn vịt bị giật mình bay mất rồi! 🦆💨",
                    color=discord.Color.red()
                )
                count = 0
                last_user_id = None
                total_errors = 0
                save_data() 
                await message.channel.send(embed=embed)
            else:
                save_data()
                await message.add_reaction('⚠️')
                embed = discord.Embed(
                    title=f"⚠️ CẢNH BÁO: ĐẾM SAI THỨ TỰ! (Tổng lỗi kênh: {total_errors}/5)",
                    description=f"{message.author.mention}, bạn đã đếm sai số thứ tự rồi!",
                    color=discord.Color.orange()
                )
                embed.add_field(name="📝 CÁCH ĐẾM ĐÚNG tiếp theo phải là:", value=f"**`{expected_text}`** hoặc **`{expected_text} con vịt`**.", inline=False)
                embed.set_footer(text="⚠️ Nếu tổng lỗi toàn server > 5 lần, đàn vịt sẽ bị Reset về 0!")
                await message.channel.send(embed=embed)
            return

        count = expected_next
        last_user_id = user_id
        save_data() 

        await message.add_reaction('✅')
        await message.add_reaction('🦆')

        await bot.process_commands(message)

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("❌ Không tìm thấy DISCORD_TOKEN! Hãy tạo file .env và điền DISCORD_TOKEN=token_cua_ban")
    else:
        try:
            bot.run(TOKEN)
        except Exception as e:
            logging.error(f"Bot dừng vì lỗi: {e}")
            print(f"❌ Bot dừng vì lỗi, xem chi tiết trong bot.log: {e}")