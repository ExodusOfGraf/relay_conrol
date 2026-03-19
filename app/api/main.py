from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import minimalmodbus
import time

app = FastAPI()

instrument = None
PORT = 'COM3'
ID = 1
# --- Модель данных для управления реле ---
class RelayControl(BaseModel):
    relay_num: int
    state: bool

# --- Функции  ---

def get_instrument():
    global instrument
    if instrument is None:
        try:
            instrument = minimalmodbus.Instrument(PORT, ID)
            instrument.serial.baudrate = 9600
            # Увеличиваем таймаут для стабильности
            instrument.serial.timeout = 0.2 
            instrument.mode = minimalmodbus.MODE_RTU
        except Exception as e:
            print(f"Ошибка инициализации порта: {e}")
    return instrument

def scan_ids():
    #print("Сканирование устройств на порту {PORT}...".format(PORT))
    found_id = {}
    for slave_id in range(1, 247):
        try:
            instrument = minimalmodbus.Instrument(PORT, slave_id)
            instrument.serial.baudrate = 9600
            instrument.serial.timeout = 0.05
            instrument.mode = minimalmodbus.MODE_RTU
            
            instrument.read_register(60002)
            print(f"Адрес найден!  ID: {slave_id}")
            found_id[slave_id] = True
        except Exception:
            pass
    if not found_id:
        print("Адреса не найдены.")
    return found_id


def get_instrument():
    global instrument
    if instrument is None:
        # для testa fix on ID=1
        try:
            instrument = minimalmodbus.Instrument(PORT, ID)
            instrument.serial.baudrate = 9600
            instrument.serial.timeout = 0.05
            instrument.mode = minimalmodbus.MODE_RTU
        except Exception as e:
            print(f"Ошибка инициализации порта: {e}")
    return instrument

def set_relay_logic(inst, relay_num, state):
    
    if 1 <= relay_num <= 16:
        reg, bit = 60016, relay_num - 1
    elif 17 <= relay_num <= 20:
        reg, bit = 60015, relay_num - 17
    else:
        raise ValueError("Реле должно быть от 1 до 20")

    current = inst.read_register(reg)
    relay_weight = 2 ** bit
    is_on = (current & relay_weight) > 0

    if state:
        new_val = current if is_on else current + relay_weight
    else:
        new_val = current - relay_weight if is_on else current
    
    inst.write_register(reg, new_val)

# Эндпоинты 

@app.get("/")
def read_root():
    return {"status": "success", "port": PORT}

@app.get("/info")
def get_info():
    """Получить напряжение и версию ПО"""
    inst = get_instrument()
    try:
        v = inst.read_register(24582, functioncode=4)
        ver = inst.read_register(60002)
        return {
            "voltage_v": v / 1000,
            "fw_version": ver / 100,
            "port": PORT
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/relay/control")
def control_relay(data: RelayControl):
    """Управление реле"""
    inst = get_instrument()
    try:
        set_relay_logic(inst, data.relay_num, data.state)
        return {"status": "success", 
                "message": f"Реле {data.relay_num} установлено в {data.state}"
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/relay/off_all")
def off_all():
    """выкл всё"""
    inst = get_instrument()
    try:
        inst.write_register(60016, 0)
        inst.write_register(60015, 0)
        return {
            "status": "success",
            "message": "Все реле выключены"                        
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/relay/health")
def health_check():
    """ статусы реле"""
    inst = get_instrument()
    try:
        group1 = inst.read_register(60016)
        group2 = inst.read_register(60015)

        health_check = {}

        for i in range(16):
            rel_numb = i + 1
            is_on = None
            if  group1 & (1 << i):
                is_on = True
                health_check[rel_numb] = True
            else:
                is_on = False
                health_check[rel_numb] = False

        for b in range(4):
            rel_numb = b + 17
            is_on = None
            if  group2 & (1 << b):
                is_on = True
                health_check[rel_numb] = True
            else:
                is_on = False
                health_check[rel_numb] = False
        
        return {
            "status": "succes   s",
            "relays": health_check
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
            

@app.get("/id")
def id_scan():
    #поиск адресов по которым можно подключиться
     inst = get_instrument()
     try:
         ids = scan_ids()
         return {
             "status": "success", 
             "ids": list(ids.keys())
             }
     except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # на порту 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)