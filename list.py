from enum import Enum
from datetime import datetime, timedelta
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler

TOKEN_BOT = "6957947683:AAFUWkXU1xDqZ7KjmU4io0XikMIAgYeL7b0"
AVAILABLE_CATEGORIES = ["Food", "Transportation", "Utilities", "Entertainment", "Other"]
user_data1 = dict()
user_data = dict()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class TimeInterval(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class Transaction:
    def __init__(self, category: str, amount: float, deadline: datetime = None):
        self.category = category
        self.amount = amount
        self.deadline = deadline
        self.timestamp = datetime.now()

    def __str__(self):
        if not self.deadline:
            deadline_info = f", Time: {self.timestamp.strftime('%Y-%m-%d')}"
            return f"{self.category} (Amount: {self.amount}{deadline_info})"
        else:
            deadline_info = f", Time: {self.deadline}" if self.deadline else ""
            return f"{self.category} (Amount: {abs(self.amount)}{deadline_info})"


async def start(update: Update, context: CallbackContext) -> None:
    logging.info("Command start was triggered")
    await update.message.reply_text(
        "Welcome to my Finance Bot\n"
        "Commands: "
        "Add expense: /add_expense <category> <amount> [| <deadline>]\n"
        "Add income: /add_income <category> <amount> [| <deadline>]\n"
        "List expenses: /list_expenses\n"
        "List incomes: /list_incomes\n"
        "Check expenses: /check_expense [day/week/month]\n"
        "Remove expense: /remove_expense\n"
        "Remove income: /remove_income\n"
        "Statistics: /statistic"
    )


async def add_expense(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    expense_parts = " ".join(context.args).split(",")

    # Return list of available categories
    categories_list = "\n".join([f"{i + 1}. {category}" for i, category in enumerate(AVAILABLE_CATEGORIES)])
    await update.message.reply_text(f"Available categories:\n{categories_list}")

    if not expense_parts:
        await update.message.reply_text("Enter the category and amount.")
        return

    category_input = expense_parts[0].strip()

    if category_input not in AVAILABLE_CATEGORIES:
        await update.message.reply_text(f"Invalid category. Available categories:\n{categories_list}")
        return

    try:
        amount_str = expense_parts[1].strip()
    except (IndexError, ValueError):
        await update.message.reply_text("Enter a valid amount.")
        return

    try:
        amount = float(amount_str)
    except ValueError:
        await update.message.reply_text("Invalid amount format. Please enter a valid number.")
        return

    deadline = None
    if len(expense_parts) > 2:
        try:
            deadline = datetime.strptime(expense_parts[2].strip(), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logging.error("Invalid deadline format")
            await update.message.reply_text("Your deadline argument is invalid, please use %Y-%m-%d %H:%M:%S format")
            return

    if not user_data.get(user_id):
        user_data[user_id] = []

    transaction = Transaction(category_input, -amount, deadline)
    user_data[user_id].append(transaction)

    await update.message.reply_text(f"Expense: {category_input}, amount {amount} was successfully added!")


async def list_expense(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if not user_data.get(user_id):
        await update.message.reply_text("You dont have any expenses")
        return

    result = "\n".join([f"{i + 1}. {t}" for i, t in enumerate(user_data[user_id])])
    await update.message.reply_text(result)


async def add_income(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    income_parts = " ".join(context.args).split(",")

    try:
        category_title = income_parts[0].strip()
        amount_str = income_parts[1].strip()
    except (IndexError, ValueError):
        await update.message.reply_text("Enter the income category and amount.")
        return

    try:
        amount = float(amount_str)
    except ValueError:
        await update.message.reply_text("Invalid amount format. Please enter a valid number.")
        return

    deadline = None
    if len(income_parts) > 2:
        try:
            deadline = datetime.strptime(income_parts[2].strip(), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logging.error("Invalid deadline format")
            await update.message.reply_text("Your deadline argument is invalid, please use %Y-%m-%d %H:%M:%S format")
            return

    if not user_data1.get(user_id):
        user_data1[user_id] = []

    transaction = Transaction(category_title, amount, deadline)
    user_data1[user_id].append(transaction)
    await update.message.reply_text(f"Transaction: {category_title}, amount {+ amount} was successfully added!")


async def list_income(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if not user_data1.get(user_id):
        await update.message.reply_text("You dont have any income")
        return

    result = "\n".join([f"{i + 1}. {t}" for i, t in enumerate(user_data1[user_id])])
    await update.message.reply_text(result)


async def check_transactions(update: Update, context: CallbackContext, user_data_dict: dict, transaction_type: str) -> None:
    user_id = update.message.from_user.id

    if not user_data_dict.get(user_id):
        await update.message.reply_text(f"You don't have any {transaction_type}s.")
        return

    try:
        now = datetime.now()

        time_interval_arg = context.args[0].lower() if context.args else TimeInterval.DAY.value
        if time_interval_arg not in [e.value for e in TimeInterval]:
            await update.message.reply_text("Invalid time interval. Available options: day, week, month.")
            return

        if time_interval_arg == TimeInterval.DAY.value:
            start_date = datetime(now.year, now.month, now.day)
        elif time_interval_arg == TimeInterval.WEEK.value:
            start_date = now - timedelta(days=8)
        elif time_interval_arg == TimeInterval.MONTH.value:
            start_date = datetime(now.year, now.month, 1) - timedelta(days=1)
        else:
            await update.message.reply_text("Invalid time interval. Available options: day, week, month.")
            return

        transactions_in_interval = []

        for transaction in user_data_dict[user_id]:
            if not transaction.deadline or start_date <= transaction.deadline <= now:
                transactions_in_interval.append(str(transaction))

        if transactions_in_interval:
            await update.message.reply_text(
                f"Transactions for the last {time_interval_arg}: {len(transactions_in_interval)}\n"
                f"{'\n'.join(transactions_in_interval)}"
            )
        else:
            await update.message.reply_text(f"You don't have any transactions for the last {time_interval_arg}.")
    except Exception as e:
        logging.error(f"An error occurred while checking transactions: {e}")
        await update.message.reply_text("An error occurred while checking transactions. Please try again later.")


async def check_expenses(update: Update, context: CallbackContext) -> None:
    await check_transactions(update, context, user_data, "expense")


async def check_incomes(update: Update, context: CallbackContext) -> None:
    await check_transactions(update, context, user_data1, "income")


async def remove_transaction(update: Update, context: CallbackContext, user_data_dict: dict, transaction_type: str) -> None:
    user_id = update.message.from_user.id

    if not user_data_dict.get(user_id):
        await update.message.reply_text(f"You don't have any {transaction_type}s.")
        return

    try:
        removed_idx = int(context.args[0]) - 1
        transaction = user_data_dict[user_id].pop(removed_idx)
        await update.message.reply_text(f"{transaction_type.capitalize()} transaction: {transaction} was successfully removed.")
    except (ValueError, IndexError):
        await update.message.reply_text("You entered an invalid index.")


async def remove_expense(update: Update, context: CallbackContext) -> None:
    await remove_transaction(update, context, user_data1, "expense")


async def remove_income(update: Update, context: CallbackContext) -> None:
    await remove_transaction(update, context, user_data1, "income")


async def statistic(update: Update, context: CallbackContext) -> None:
    await check_transactions(update, context, user_data, "expense")
    await check_transactions(update, context, user_data1, "income")


def run():
    app = ApplicationBuilder().token(TOKEN_BOT).build()
    logging.info("Application build successfully!")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("add_expense", add_expense))
    app.add_handler(CommandHandler("add_income", add_income))
    app.add_handler(CommandHandler("list_expenses", list_expense))
    app.add_handler(CommandHandler("list_incomes", list_income))
    app.add_handler(CommandHandler("check_expense", check_expenses))
    app.add_handler(CommandHandler("check_income", check_incomes))
    app.add_handler(CommandHandler("remove_expense", remove_expense))
    app.add_handler(CommandHandler("remove_income", remove_income))
    app.add_handler(CommandHandler("statistic", statistic))
    app.run_polling()


if __name__ == "__main__":
    run()
