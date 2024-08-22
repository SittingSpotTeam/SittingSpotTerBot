from telegram.ext import *
from telegram import *
import requests
import json

token = "7519043483:AAFYDZIvPif6PaFqTUjLIzujwVH8NywjId4"
demo_x=11.12
demo_y=46.07
demo_range=50

search_url="http://localhost:8086/api/v1/"
review_url="http://localhost:8084/api/v1"

starting_range = 10

REVIEW = 1

bot=None

async def addReview(update, context):
    query = update.callback_query
    #print(query,flush=True)
    data = json.loads(query.data)
    if data["action"] == "add":
        print("post review for "+data["id"])
        context.chat_data["spotId"] = data["id"]
        context.chat_data["addingReview"] = True

        #response = requests.post(review_url, data={"sittingSpotId":})
        await update._bot.send_message(
                update.effective_message.chat_id,
                message_thread_id=update.effective_message.message_thread_id,
                text="Write now your review")
    if data["action"] == "get":
        print("get review for "+data["id"])
        response = requests.get(review_url+"?id="+data["id"])

        for r in list(response.json()):
            await update._bot.send_message(
                update.effective_message.chat_id,
                message_thread_id=update.effective_message.message_thread_id,
                text=r["corpus"])


async def review(update, context):
    if context.chat_data["addingReview"]:
        headers = {'content-type': 'application/json'}
        review_text = update.message.text
        print({"sittingSpotId":context.chat_data["spotId"],"corpus":review_text})
        response = requests.post(review_url+"/"+context.chat_data["spotId"], data=review_text,headers=headers)
        context.chat_data["addingReview"] = False


# execute the first search with a range of 10 meters and store the user location
# in case he wants to search again
async def search(update, context):
    #await update.message.edit_reply_markup()
    user_location = update.message.location
    response = requests.get(search_url+f"?area={starting_range}&x={user_location.longitude}&y={user_location.latitude}")
    print(update.message.location)

    context.chat_data["last_location"] = user_location
    context.chat_data["n_searches"] = 1

    keyboard = [[InlineKeyboardButton(text="Search wider",callback_data="wider")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if list(response.json()) == []:
        await update.message.reply_text("Sorry, no spot found.",reply_markup=reply_markup)
        await update.message.reply_text(f"Searched in {starting_range} meters.")
        return
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
    await update.message.reply_text(f"Found {len(list(response.json()))} spots.",reply_markup=reply_markup)
    await update.message.reply_text(f"Searched in {starting_range} meters.")


# does second and successive searched maintaing the same center but increasing 
# the range at each repetition
async def widerSearch(update, context):
    
    user_location = context.chat_data["last_location"]
    context.chat_data["n_searches"] = context.chat_data["n_searches"] + 1
    multiplier = context.chat_data["n_searches"]

    response = requests.get(search_url+f"?area={starting_range*multiplier}&x={user_location.longitude}&y={user_location.latitude}")

    keyboard = [[InlineKeyboardButton(text="Search wider",callback_data="wider")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if list(response.json()) == []:
        await update._bot.send_message(
                update.effective_message.chat_id,
                message_thread_id=update.effective_message.message_thread_id,
                text="Sorry, no spot found.",
                reply_markup=reply_markup,
            )
        await update._bot.send_message(
                update.effective_message.chat_id,
                message_thread_id=update.effective_message.message_thread_id,
                text=f"Searched in {starting_range*multiplier} meters.",
            )
        #await update.callback_query.reply_text("Sorry, no spot found.")
        return
    for d in list(response.json()):
        await update._bot.send_location(
            update.effective_message.chat_id,
            message_thread_id=update.effective_message.message_thread_id,
            latitude=d["location"]["y"],
            longitude=d["location"]["x"], 
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Add Review", callback_data=json.dumps({"id":d["spotId"],"action":"add"})),
                InlineKeyboardButton("Get Reviews", callback_data=json.dumps({"id":d["spotId"],"action":"get"})),
                ]]),
            )
    await update._bot.send_message(
        update.effective_message.chat_id,
        message_thread_id=update.effective_message.message_thread_id,
        text=f"Found {len(list(response.json()))} spots.",
        reply_markup=reply_markup,
        )
    await update._bot.send_message(
                update.effective_message.chat_id,
                message_thread_id=update.effective_message.message_thread_id,
                text=f"Searched in {starting_range*multiplier} meters.",
            )
    #await update.callback_query.reply_text(f"Found {len(list(response.json()))} spots.",reply_markup=reply_markup)


# handler to request the location to the user after he decides to do a search
async def requestLocation(update, context):
    keyboard = [[KeyboardButton(text="Send Your Location", request_location=True),]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(f'Give your current location to perform the search',reply_markup=reply_markup)


async def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("Submission of review canceled.", reply_markup=ReplyKeyboardRemove())
    context.chat_data["addingReview"]


def main():
    
    application = Application.builder().token(token).concurrent_updates(False).read_timeout(30).write_timeout(30).build()
    application.arbitrary_callback_data = True
    application.add_handler(CommandHandler("search", requestLocation))
    application.add_handler(CallbackQueryHandler(callback=widerSearch,pattern="^wider$"))
    application.add_handler(MessageHandler(filters.LOCATION,search))
    application.add_handler(CallbackQueryHandler(callback=addReview)) #pattern="Add Review")
    #application.add_handler(CallbackQueryHandler(callback=getReview,pattern="Get Reviews"))
    application.add_handler(MessageHandler(filters.TEXT, review))
    print("Telegram Bot started!", flush=True)
    application.run_polling()


if __name__ == '__main__':
    main()