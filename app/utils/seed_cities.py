from app import db
from app.models import City

CITY_NAMES = [
    "Agartala",
    "Agra",
    "Ahmedabad",
    "Alleppey",
    "Amritsar",
    "Bangalore",
    "Bhopal",
    "Bhubaneswar",
    "Bir Billing",
    "Chandigarh",
    "Chennai",
    "Coimbatore",
    "Coorg",
    "Cuttack",
    "Darjeeling",
    "Dehradun",
    "Delhi",
    "Dharamshala",
    "Faridabad",
    "Ghaziabad",
    "Goa",
    "Gokarna",
    "Gurgaon",
    "Guwahati",
    "Gwalior",
    "Hampi",
    "Hyderabad",
    "Indore",
    "Jaipur",
    "Jodhpur",
    "Kalaburagi",
    "Kochi",
    "Kolkata",
    "Kota",
    "Leh",
    "Lucknow",
    "Manali",
    "Mangalore",
    "Mathura",
    "Mount Abu",
    "Mumbai",
    "Mussoorie",
    "Mysore",
    "Nagpur",
    "Nainital",
    "Noida",
    "Pondicherry",
    "Pune",
    "Puri",
    "Raipur",
    "Rishikesh",
    "Rourkela",
    "Shimla",
    "Siliguri",
    "Surat",
    "Trivandrum",
    "Udaipur",
    "Udupi",
    "Vadodara",
    "Varanasi",
    "Varkala",
]


def seed_cities() -> None:
    existing = {city.name for city in City.query.all()}
    new_cities = [City(name=name) for name in CITY_NAMES if name not in existing]

    if not new_cities:
        return

    db.session.bulk_save_objects(new_cities)
    db.session.commit()
