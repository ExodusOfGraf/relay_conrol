from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
'''
main =  ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Получить напряжение и версию ПО")],
                                      [KeyboardButton(text="Управление реле")], 
                                        [KeyboardButton(text="Cостояние реле")], 
                                        [KeyboardButton(text="Выключить все реле")]], resize_keyboard=True)
'''

main = InlineKeyboardButton(text="Меню упр. реле")
