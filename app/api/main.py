from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import minimalmodbus
import time
import threading
serial_lock = threading.Lock() #чтобы не было raise exeption

app = FastAPI()

instrument = None
PORT = 'COM3'
ID = 1 #временно, пока не реализую нормальную систему поиска и смены id для подключ.


# --- МОдели ---
class RelayControl(BaseModel):
    relay_num: int
    state: bool

class IDChange(BaseModel):
    new_id: int

class PortChange(BaseModel):
    new_port: str

class SHIMControl(BaseModel):
    relay_num: int
    duty_cycle: int # 0-1000 это 100% мощности
# --- Функции  ---

def scan_ids():
    
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
    #Если порт был изменен в эндпоинте, instrument станет None 
    if instrument is None:
        try:
            instrument = minimalmodbus.Instrument(PORT, ID)
            instrument.serial.baudrate = 9600
            instrument.serial.timeout = 0.2
            instrument.mode = minimalmodbus.MODE_RTU
        except Exception as e:
            raise Exception(f"Ошибка открытия {PORT}: {e}")
    
    instrument.address = ID
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
    with serial_lock:
        try:
            v = inst.read_register(24582, functioncode=4)
            ver = inst.read_register(60002)
            return {
                "voltage_v": v / 1000,
                "fw_version": ver / 100
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/relay/control")
def control_relay(data: RelayControl):
    """Управление реле"""
    inst = get_instrument()
    with serial_lock:
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
    with serial_lock:
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
    with serial_lock:
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
                "status": "success",
                "relays": health_check
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            

@app.get("/id")
def id_scan():
    #поиск адресов по которым можно подключиться
    inst = get_instrument()
     
    with serial_lock:
         try:
             ids = scan_ids()
             return {
                 "status": "success", 
                 "ids": list(ids.keys())
                 }
         except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
     
@app.post("/id/set_id")
def set_id(data: IDChange):
    global ID
    if not (1 <= data.new_id <= 247):
        raise HTTPException(status_code=400, detail="ID от 1 до 247")
    
    ID = data.new_id
    #обнов адрес в объекте если он уже создан
    if instrument:
        instrument.address = ID
    return {"message": f"ID успешно изменен на {ID}"}


@app.post("/port/set_port")
def set_port(data: PortChange):
    global PORT, instrument
    new_p = data.new_port.upper()
    
    if instrument:
        try:
            instrument.serial.close()
        except:
            pass
        instrument = None # get_instrument создаст новый с нов. портом
    
    PORT = new_p
    return {"message": f"Порт изменен на {PORT}. Подключение будет пересоздано при следующем запросе"}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
