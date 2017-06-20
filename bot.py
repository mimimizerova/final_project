import telebot
import conf
import random
import shelve
from telebot import types

bot = telebot.TeleBot(conf.TOKEN)

with open('questions.csv', 'r', encoding='utf-8') as f:
    questions = {}  
    for line in f:
        num, text = line.strip().split(';')[0], line[2:len(line)-1]
        questions[num] = text
keys = list(questions.keys())  

def set_user_question(chat_id, num, i):
    with shelve.open('data.db') as storage:
        storage[str(chat_id)] = [num, i]
        
def get_user_question(chat_id):
    with shelve.open('data.db') as storage:
        try:
            arr = storage[str(chat_id)]
            return arr
        # Если человека нет в базе, ничего не возвращаем
        except KeyError:
            return None

keyboard1 = types.ReplyKeyboardMarkup(row_width=2)
btn1 = types.KeyboardButton('+')
btn2 = types.KeyboardButton('-')
keyboard1.add(btn1, btn2)

keyboard2 = types.ReplyKeyboardMarkup(row_width=2)
btn1 = types.KeyboardButton('да')
btn2 = types.KeyboardButton('нет')
keyboard2.add(btn1, btn2)

@bot.message_handler(commands=['start'])
def send_first_question(message):
    question_num = random.choice(keys)
    q = questions[question_num].split(';')
    bot.send_message(message.chat.id, q[0], reply_markup=keyboard1)
    set_user_question(message.chat.id, question_num, 0)
        
@bot.message_handler(regexp='[-+]')        
def get_one_question(message):
    question_num = get_user_question(message.chat.id) 
    if question_num:
        with open('results.csv', 'a', encoding = 'utf-8') as results:
            results.write(message.text +';')
        q = questions[question_num[0]].split(';')
        i = question_num[1]
        if i<len(q)-1:
            bot.send_message(message.chat.id, q[i+1], reply_markup=keyboard1)
            set_user_question(message.chat.id, question_num[0], i+1)
        elif i>=len(q)-1:
            with open('results.csv', 'a', encoding = 'utf-8') as results:
                results.write(question_num[0]+'\n')
            bot.send_message(message.chat.id, 'Вы ответили на вопрос! Хотите ещё?', reply_markup=keyboard2)
    else:
        bot.send_message(message.chat.id, 'Что-то пошло не так... /start')
        
@bot.message_handler(regexp='да')
def get_other_questions(message):
    question_num = get_user_question(message.chat.id) 
    if question_num:
        if len(keys) != 1:
            keys.remove(question_num[0])
            new_question_num = random.choice(keys)
            q = questions[new_question_num].split(';')
            bot.send_message(message.chat.id, q[0], reply_markup=keyboard1)
            set_user_question(message.chat.id, new_question_num, 0)
        elif len(keys) == 1:
            bot.send_message(message.chat.id, 'Кажется, Вы ответили на все вопросы... Быть может, вы хотите ещё?', reply_markup=keyboard2)
    else:
        bot.send_message(message.chat.id, 'Что-то пошло не так... /start')

@bot.message_handler(commands=['stat'])
def show_me_statistics(message):
    question_num = get_user_question(message.chat.id)
    if question_num:
        with open('results.csv', 'r', encoding='utf-8') as r:
            n = 0
            A = []
            stats = []
            for line in r:
                if line.endswith(question_num[0]+'\n'):
                    n+=1
                    A.append(line.split(';')[:len(line.split(';'))-1])
            for j in range (len(A[0])):
                p = 0
                for el in A:
                    if el[j] == '+':
                        p+=1
                stats.append((p/n)*100)
        q = questions[question_num[0]].split(';')
        stat_string = ''
        for k in range (len(q)):
            stat_string+= q[k]+ ': ' +str(round(stats[k]))+'%' + '\n'
        bot.send_message(message.chat.id, stat_string)
    else:
        bot.send_message(message.chat.id, 'Что-то пошло не так... /start')

        
                          

@bot.message_handler(regexp='нет')
def stop_it(message):
    bot.send_message(message.chat.id, 'Очень жаль... Но спасибо вам, что уделили время этому опросу!) Если захотите продолжить, наберите "Да"')
    
@bot.message_handler(func=lambda m: True)
def what(message):
    bot.send_message(message.chat.id, 'Боюсь, я могу отвечать только на +, -, да и нет. Не пишите мне других сообщений! Если что-то непонятно, воспользуйтесь командой /help')

    

if __name__ == '__main__':
    bot.polling(none_stop=True)

