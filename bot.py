import telebot
import conf
import random
import shelve
from telebot import types
import flask

WEBHOOK_URL_BASE = "https://{}:{}".format(conf.WEBHOOK_HOST, conf.WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(conf.TOKEN)

bot = telebot.TeleBot(conf.TOKEN, threaded = False)
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH)

app = flask.Flask(__name__)


with open('questions.csv', 'r', encoding='utf-8') as f:
    questions = {}  
    for line in f:
        num, text = num, text = line.strip().split(';')[0], line[len(line.strip().split(';')[0])+1:len(line)-1]
        questions[num] = text
keys = list(questions.keys())

docs = ['https://docs.google.com/forms/d/e/1FAIpQLSePthyfJADge--1UZFNStTufL9sNWoImt-vsmifNwcSB_aZVw/viewform?c=0&w=1',
        'https://docs.google.com/forms/d/e/1FAIpQLSc-SUfdl4fOlqF2ueecLa06YkgQ3rui-0WjlFAV1muLb2PVyw/viewform?c=0&w=1',
        'https://docs.google.com/forms/d/e/1FAIpQLSfmbBP5jRuSwc0agCK3zanI95MxZaMGl8mmVPf624jHigA9xw/viewform?c=0&w=1',
        'https://docs.google.com/forms/d/e/1FAIpQLSdFo_EcG9Y4pvGilIFkh8_ETjKa2IfSI4y6xaUpvXnUy388Lg/viewform?c=0&w=1',
        'https://docs.google.com/forms/d/e/1FAIpQLSeDtksBo6t0TttUtzqEyo_aKbtcyG-aPqT4ILPaLS01PF4WxA/viewform?c=0&w=1']

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

@bot.message_handler(commands=['help'])
def some_instructions(message):
    bot.send_message(message.chat.id, 'А вы знали, что если вы напишите мне /docs, то перед вами откроется великолепная возмоность поучаствовать в заполнении интереснейшего гугл-дока?')
    bot.send_message(message.chat.id, 'Выбрав да или нет, можно продолжить оценивать предложения или расстаться со мной навсегда :с. Ну или только на время, потому что написав мне "да", вы всегда сможете продолжить')
    bot.send_message(message.chat.id, 'Я не боюсь непонятных сообщений и смайликов. Я боюсь лишних + и -, а также преждевременных да или нет. Пожалуйста, следуйте чёткому правилу: одно предложение - одна оценка, т.е. один знак + или -!')
                     


@bot.message_handler(commands=['start'])
def send_first_question(message):
    question_num = random.choice(keys)
    q = questions[question_num].split(';')
    bot.send_message(message.chat.id, 'Доброго времени суток! Я буду присылать Вам предложения, а вы будете с помощью кнопок "+" и "-" оценивать, грамматичны они или нет. Каждые несколько предложений составляют блок из одного вопроса. \nПожалуйста, не используйте никакие функции и не пишите "да" и "нет" во время ответа на один вопрос, это может меня сломать :с \n После того, как вы ответите на первый вопрос, вам будут предложены другие опции, но пока что я очень прошу вас нажимать на кнопки + или -. Выберите +, если предложение кажется вам правильным и -, если предложение кажется вам неправильным: ')
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
            bot.send_message(message.chat.id, 'Вы ответили на вопрос! Чтобы посмотреть статистику ответов по этому вопросу, напишите мне /stat. \n Если вы хотите продолжить оценивать предложения, нажмите кнопку "да".', reply_markup=keyboard2)
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
            bot.send_message(message.chat.id, 'Кажется, Вы ответили на все вопросы... Быть может, вы хотите заполнить гугл-док с похожими вопросами? Тогда наберите /docs', reply_markup=keyboard2)
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
                    try:
                        if el[j] == '+':
                            p+=1
                    except:
                        bot.send_message(message.chat.id, 'Что-то пошло не так... /start')
                stats.append((p/n)*100)
        q = questions[question_num[0]].split(';')
        stat_string = ''
        for k in range (len(q)):
            stat_string+= q[k]+ ': ' +str(round(stats[k]))+'%' + '\n'
        bot.send_message(message.chat.id, stat_string)
    else:
        bot.send_message(message.chat.id, 'Что-то пошло не так... /start')

@bot.message_handler(commands=['docs'])
def send_doc(message):
    if docs != []:
        link = docs.pop()
        bot.send_message(message.chat.id, link)
    else:
        bot.send_message(message.chat.id, 'Похоже, мне нечего больше вам предложить. Большое спасибо за помощь науке!')
       
                          

@bot.message_handler(regexp='нет')
def stop_it(message):
    bot.send_message(message.chat.id, 'Что ж... На нет и суда нет) Спасибо вам, что уделили время оцениванию предложений!) Если захотите продолжить, я буду здесь. Просто нажмите кнопку "да"')
    
@bot.message_handler(func=lambda m: True)
def what(message):
    bot.send_message(message.chat.id, 'Боюсь, я умею отвечать только на +, -, да и нет. Если что-то непонятно, воспользуйтесь командой /help')

    

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'ok'


@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


