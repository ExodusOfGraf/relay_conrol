from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

class RelayTask(CallbackData, prefix="rel"):
    id: int      #номер реле
    state: bool  #состояние 

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="Статус системы", callback_data="status_info")
    builder.button(text="Управление реле", callback_data="manage_relays")
    builder.button(text="Выключить всё", callback_data="off_all")
    builder.adjust(1)
    return builder.as_markup()

def get_relays_grid(relays_dict: dict):
    #создает сетку кнопок по словарю из /relay/health
    builder = InlineKeyboardBuilder()
    
    sorted_relays = sorted(relays_dict.items(), key=lambda x: int(x[0]))
    
    for relay_num, is_on in sorted_relays:
        icons = "🟢" if is_on else "🔴"
        label = f"{icons} {relay_num}"
        # инвентируется в хендлере
        builder.button(
            text=label, 
            callback_data=RelayTask(id=int(relay_num), state=is_on)
        )
    
    builder.adjust(4) # 4 кнопки в ряду
    builder.row(InlineKeyboardBuilder().button(text="Назад", callback_data="main_menu").button)
    return builder.as_markup()