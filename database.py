from supabase import create_client
import streamlit as st

def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)
def insert_customer(name: str, email: str, phone: str):
    supabase = get_supabase_client()
    response = supabase.table("customers").insert({
        "name": name,
        "email": email,
        "phone": phone
    }).execute()
    return response.data[0]["customer_id"]


def insert_booking(customer_id: str, room_type: str, check_in: str, check_out: str):
    supabase = get_supabase_client()
    response = supabase.table("bookings").insert({
        "customer_id": customer_id,
        "room_type": room_type,
        "check_in": check_in,
        "check_out": check_out
    }).execute()
    return response.data[0]["id"]


def get_all_bookings():
    supabase = get_supabase_client()
    response = supabase.table("bookings").select(
        "id, room_type, check_in, check_out, status, created_at, customers(name, email)"
    ).execute()
    return response.data
