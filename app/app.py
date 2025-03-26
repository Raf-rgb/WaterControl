import time
import logging
import streamlit as st

from datetime import datetime
from utils.utils import turn_on_pump, turn_off_pump, insert_document, is_summer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(
    page_title='Water Control',
    page_icon='💧',
    layout='centered'
)

# Inicializamos el estado de ciclos y la bandera de parada
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None

if "cycles" not in st.session_state:
    st.session_state["cycles"] = 1

if "stop_flag" not in st.session_state:
    st.session_state["stop_flag"] = False

if "total_cycles" not in st.session_state:
    st.session_state["total_cycles"] = 0

if "usage_data" not in st.session_state:
    st.session_state["usage_data"] = None

def sleep_with_stop(total_seconds):
    for _ in range(int(total_seconds)):
        if st.session_state.get("stop_flag", False):
            return False
        time.sleep(1)
    return True

def insert_data(total_cycles:int):
    try:
        end_time    = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time  = datetime.strptime(st.session_state.start_time, '%Y-%m-%d %H:%M:%S')
        end_time_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

        total_time_usage = (end_time_dt - start_time).total_seconds()
        electricity_cost = st.secrets.app_config.electricity_rate_summer if is_summer(end_time_dt) else st.secrets.app_config.electricity_rate

        st.session_state.usage_data = {
            "start_time": st.session_state.start_time,
            "end_time": end_time,
            "total_seconds_usage": total_time_usage,
            "total_seconds_process": total_time_usage + st.secrets.app_config.minutes_to_rest * (total_cycles - 1),
            "cycles": total_cycles,
            "cost": (st.secrets.app_config.kwh_per_hour / 60) * (total_time_usage / 60) * electricity_cost
        }

        insert_document(
            st.secrets.mongo_secrets.database_name,
            st.secrets.mongo_secrets.collection_name,
            st.session_state.usage_data
        )
    except Exception as e:
        logging.error(f'Error inserting data: {e}')

def start_pump_process():
    max_cycles = st.secrets.app_config.max_cycles_usage

    if st.session_state.start_time is None:
        st.session_state.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with st.status('🟢 Bombeando agua...', expanded=True):
        while st.session_state.cycles <= max_cycles and not st.session_state.get("stop_flag", False):
            logging.info(f"💧 Starting pump (Cycle {st.session_state.cycles})...")

            turn_on_pump()

            st.success(f"💧 Ciclo {st.session_state.cycles} iniciado!")

            if not sleep_with_stop(st.secrets.app_config.max_minutes_usage * 60):
                break

            logging.info("🔌 Stopping pump...")
            turn_off_pump()

            if st.session_state.cycles < max_cycles:
                logging.info(f"🛏️ Resting for {st.secrets.app_config.minutes_to_rest} minutes...")
                st.warning(f"🛏️ Descansando por {st.secrets.app_config.minutes_to_rest} minutos...")
                
                if not sleep_with_stop(st.secrets.app_config.minutes_to_rest * 60):
                    break
            
            st.session_state.cycles += 1

    if st.session_state.cycles > max_cycles and not st.session_state.get("stop_flag", False):
        logging.info(f"🏁 All cycles completed. Stopping pump process...")
        st.success("🏁 Todos los ciclos permitidos se han completado!")
        insert_data(max_cycles)
        st.rerun()

def stop_pump_process():
    logging.info('🛑 Stop command received. Stopping pump process...')

    st.session_state["stop_flag"] = True

    turn_off_pump()

    st.session_state.total_cycles = st.session_state.cycles

    insert_data(st.session_state.total_cycles)

    st.session_state.cycles = st.secrets.app_config.max_cycles_usage + 1

    st.rerun()

def show_data_process():
    logging.info('Showing data...')

def show_water_control():
    st.header('🐳 Water Control')
    st.divider()
    
    col_start, col_stop, col_data = st.columns(3)

    with col_start:
        start_btn = st.button('Iniciar', type="primary", use_container_width=True, key='start_pump')

    with col_stop:
        stop_btn  = st.button('Detener', use_container_width=True, key='stop_pump')
    
    with col_data:
        data_btn  = st.button('Mostrar datos', use_container_width=True, key='show_data')
    
    if start_btn:
        st.session_state["stop_flag"] = False
        st.session_state["cycles"] = 1
        start_pump_process()
    
    if stop_btn:
        stop_pump_process()
    
    if data_btn:
        show_data_process()

    if st.session_state.stop_flag:
        st.warning('🛑 Bombeo de agua detenido!')

    if st.session_state.usage_data:
        with st.expander("ℹ️ Datos de uso", expanded=True):
            hours        = int(st.session_state.usage_data['total_seconds_usage'] / 3600)
            minutes      = int((st.session_state.usage_data['total_seconds_usage'] % 3600) / 60)
            seconds      = int(st.session_state.usage_data['total_seconds_usage'] % 60)
            time_message = ""

            if hours > 0:
                time_message += f"{hours} horas, "

            if minutes > 0:
                time_message += f"{minutes} minutos y "

            if seconds > 0:
                time_message += f"{seconds} segundos."

            st.markdown(f"**Inicio:** {st.session_state.usage_data['start_time']}")
            st.markdown(f"**Fin:** {st.session_state.usage_data['end_time']}")
            st.markdown(f"**Tiempo de uso:** {time_message}")
            st.markdown(f"**Tiempo total de proceso:** {time_message}")
            st.markdown(f"**Ciclos:** {st.session_state.usage_data['cycles']}")
            st.markdown(f"**Costo:** ${st.session_state.usage_data['cost']}")
            st.markdown('---')

if __name__ == '__main__':
    show_water_control()