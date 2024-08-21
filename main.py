from telegram.ext import *
from telegram import *
import requests

token = "7519043483:AAFYDZIvPif6PaFqTUjLIzujwVH8NywjId4"
demo_x=11.12
demo_y=46.07
demo_range=50

search_url="http://localhost:8086/api/v1/"
review_url="http://localhost:8084/api/v1"


REVIEW = 1

async def addReview(update, context):
    query = update.callback_query
    print(query.query,flush=True)
    print("post review for "+query.data)
    context.chat_data["spotId"] = query.data
    #response = requests.post(review_url, data={"sittingSpotId":})
    await update.message.reply_text(
        "Write now your review, use /cancel to cancel the submission"
    )
    return REVIEW


async def getReview(update, context):
    query = update.callback_query
    print("get review for "+query.data)
    response = requests.get(review_url+"?id="+query.data)

    for r in list(response.json()):
        await update.message.reply_text(r["corpus"])


async def review(update, context):
    review_text = update.message.text
    response = requests.post(review_url, data={"sittingSpotId":context.chat_data["spotId"],"corpus":review_text})
    return ConversationHandler.END


async def search(update, context):
    response = requests.get(search_url+f"?area={demo_range}&x={demo_x}&y={demo_y}")
    print(update.message.location)
    if list(response.json()) == []:
        await update.message.reply_text("Sorry, no spot found.")
    for d in list(response.json()):
        await update.message.reply_location(
            latitude=d["location"]["y"],
            longitude=d["location"]["x"], 
            reply_markup=InlineKeyboardMarkup(
                    [[
                    InlineKeyboardButton("Add Review", callback_data=d["spotId"]),
                    InlineKeyboardButton("Get Reviews", callback_data=d["spotId"]),
                    ]]
                ))


async def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Submission of review canceled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    application = Application.builder().token(token).concurrent_updates(False).read_timeout(30).write_timeout(30).build()
    application.add_handler(CommandHandler("search", search))
    application.add_handler(InlineQueryHandler(callback=addReview)) #pattern="Add Review")
    #application.add_handler(InlineQueryHandler(callback=getReview,pattern="Get Reviews"))
    application.add_handler(ConversationHandler(
        entry_points=[InlineQueryHandler(callback=addReview,pattern="Add Review")],
        states={
            REVIEW: [MessageHandler(filters.TEXT, review)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=False,
        per_user=True
        ))
    print("Telegram Bot started!", flush=True)
    application.run_polling()


if __name__ == '__main__':
    main()