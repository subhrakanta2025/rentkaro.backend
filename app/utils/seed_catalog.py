from app import db
from app.models.catalog import CatalogBrand, CatalogModel
from flask import current_app

bike_catalog = {
    "Gravton Motors": ["Quanta"],
    "Simple Energy": ["One"],
    "Okaya": ["Classiq"],
    "Oben Electric": ["Rorr"],
    "Ola Electric": ["S1", "S1 Pro"],
    "Revolt": ["RV300", "RV400"],
    "Okinawa": [
        "Praise", "Okhi 90", "i-Praise", "Ridge +",
        "R30", "Dual", "Lite"
    ],
    "Hero Electric": [
        "NYX HX", "Photon HX", "Flash LX",
        "Atria LX", "Optima HX"
    ],
    "Crayon Motors": ["Envy"],
    "22Kymco": ["Flow"],
    "Kabira Mobility": ["KM 3000", "KM 4000"],
    "One Moto": ["Electa"],
    "Odysse": ["Evoqis", "V2", "Racer"],
    "Li-ions Elektrik": ["Spock"],
    "Tork Motors": ["Kratos"],
    "EeVe": ["Soul"],
    "BGauss": ["A2", "B8", "D15"],
    "Nexzu Mobility": ["Dextro", "Dextro +"],
    "Bajaj": [
        "CT 100", "CT 110", "Chetak",
        "Platina 100", "Platina 110",
        "Pulsar 125", "Pulsar 150", "Pulsar 180",
        "Pulsar 220", "Pulsar NS125", "Pulsar NS160",
        "Pulsar N250", "Pulsar RS200",
        "Pulsar F250", "Dominar 250", "Dominar 400",
        "Avenger Street 160", "Avenger Street 220",
        "Avenger Cruise 220"
    ],
    "Hero": [
        "HF 100", "HF Deluxe", "HF Deluxe i3s",
        "Splendor +", "Splendor Pro", "Splendor iSmart",
        "Passion Pro i3S", "Glamour 125",
        "Super Splendor", "Pleasure + 110",
        "Maestro Edge", "Maestro Edge 125",
        "Destini 125", "Xtreme 160R", "Xtreme 200S",
        "XPulse 200", "XPulse 200T", "XPulse 200 4V"
    ],
    "TVS": [
        "Sport", "Star City +", "Radeon",
        "Victor", "Raider",
        "Apache RTR 160", "Apache RTR 160 4V",
        "Apache RTR 165 RP", "Apache RTR 180",
        "Apache RTR 200 4V", "Apache RTR 200 FI E100",
        "Apache RR 310",
        "XL 100", "Scooty Pep +", "Scooty Zest 110",
        "Jupiter", "Jupiter 125",
        "Ntorq 125", "iQube"
    ],
    "Honda": [
        "CD 110 Dream", "Livo", "Shine",
        "SP 125", "Unicorn 160", "X-Blade",
        "Hornet 2.0", "CB200X",
        "CB300R", "CB350 RS", "Hness CB350",
        "Activa 6G", "Activa 125",
        "Dio", "Grazia",
        "CB500X", "CB650R", "CBR650R",
        "CB1000R +", "CBR1000RR",
        "Africa Twin", "Gold Wing"
    ],
    "Yamaha": [
        "Fascino 125", "Ray ZR 125",
        "MT-15", "MT-15 V2",
        "R15 V3", "R15 V4",
        "FZ V3", "FZ S V3", "FZ-X",
        "FZ 25", "FZS 25", "Fazer 25",
        "Aerox 155", "MT-09", "YZF R1"
    ],
    "Suzuki": [
        "Access 125", "Avenis", "Burgman",
        "Gixxer", "Gixxer SF",
        "Gixxer 250", "Gixxer SF 250",
        "Intruder", "V-Strom SX 250",
        "V-Strom 650XT", "Hayabusa"
    ],
    "Royal Enfield": [
        "Bullet 350", "Classic 350", "Classic Chrome",
        "Meteor 350", "Himalayan", "Scram 411",
        "Interceptor 650", "Continental GT 650"
    ],
    "KTM": [
        "125 Duke", "200 Duke", "250 Duke",
        "390 Duke", "790 Duke",
        "RC 125", "RC 200", "RC 390",
        "250 Adventure", "390 Adventure"
    ],
    "Kawasaki": [
        "KLX 110", "KLX 140G", "KLX 450R",
        "Ninja 300", "Ninja 400", "Ninja 650",
        "Ninja 1000", "Ninja ZX-6R",
        "Ninja ZX-10R", "Ninja ZX-10RR",
        "Ninja ZX-14R",
        "Z250", "Z650", "Z650RS", "Z900", "Z900RS",
        "Z1000", "Z1000R", "Z H2",
        "Versys X-300", "Versys 650", "Versys 1000",
        "Vulcan S", "W800 Street",
        "Ninja H2", "Ninja H2 SX", "Ninja H2R"
    ],
    "BMW": [
        "G 310 R", "G 310 GS",
        "F900R", "F900XR",
        "S 1000 R", "S 1000 RR", "S 1000 XR",
        "R nine T", "R nineT Scrambler",
        "R 1200 R", "R 1200 RS", "R 1200 GS",
        "R 1200 GS Adventure", "R 1200 RT",
        "R 1250 R", "R 1250 GS",
        "R 1250 GS Adventure", "R 1250 RT",
        "R 18",
        "K 1600", "K 1600 B", "K 1600 GTL",
        "M 1000 RR", "C 400 GT"
    ],
    "Ducati": [
        "Monster", "Monster 797", "Monster 821", "Monster 1200",
        "Scrambler", "Scrambler Desert Sled", "Scrambler 1100",
        "Hypermotard", "Hypermotard 950",
        "SuperSport", "Diavel 1260", "XDiavel",
        "Multistrada 950", "Multistrada 1200",
        "Multistrada 1200 Enduro", "Multistrada 1260",
        "Multistrada V2", "Multistrada V4",
        "Panigale V2", "Panigale V4", "1299 Panigale",
        "959 Panigale", "Streetfighter V4"
    ],
    "Harley-Davidson": [
        "Iron 883", "Forty-Eight", "1200 Custom",
        "Roadster", "Street Bob", "Fat Bob",
        "Fat Boy", "Softail Deluxe",
        "Heritage Softail Classic",
        "Sportster S", "Pan America 1250",
        "Road King", "Street Glide Special",
        "Road Glide Special", "CVO Limited"
    ],
    "Triumph": [
        "Street Twin", "Street Scrambler",
        "Street Triple", "Speed Twin",
        "Speed Triple 1200 RS",
        "Trident 660", "Tiger 850 Sport",
        "Tiger Sport 660", "Tiger 900",
        "Tiger 1200", "Rocket 3",
        "Bonneville T100", "Bonneville T120",
        "Bonneville Bobber", "Thruxton R"
    ],
    "Indian": [
        "Scout", "Scout Sixty", "Scout Bobber",
        "Chief Classic", "Chief Dark Horse",
        "Chief Vintage", "Chieftain",
        "Chieftain Dark Horse", "Chieftain Elite",
        "Roadmaster", "Roadmaster Elite",
        "Springfield", "Super Chief Limited",
        "FTR 1200"
    ],
    "Aprilia": [
        "SR 125", "SR 150", "SR 160",
        "SXR 125", "SXR 160",
        "Tuono 660", "Tuono V4",
        "RS 660", "RSV4"
    ],
    "Moto Guzzi": [
        "V85 TT", "V9 Roamer", "V9 Bobber",
        "Audace", "MGX-21", "Eldorado"
    ],
    "Benelli": [
        "Leoncino", "Leoncino 250",
        "Imperiale 400", "BN 302R",
        "TRK 251", "TRK 502", "502C",
        "TNT 600i"
    ],
    "CFMoto": [
        "300NK", "650NK", "650MT", "650GT"
    ],
    "MV Agusta": [
        "Brutale 800", "Brutale 800 RR",
        "Brutale 1090",
        "F3 800 RC", "F4 RR",
        "Turismo Veloce 800",
        "Dragster 800 RR"
    ]
}

car_catalog = {
    "Maruti Suzuki": [
        "Alto K10", "S-Presso", "Celerio", "Wagon R",
        "Ignis", "Swift", "Baleno", "Dzire", "Ciaz",
        "Fronx", "Brezza", "Ertiga", "XL6",
        "Grand Vitara", "Jimny", "Invicto", "Eeco"
    ],
    "Hyundai": [
        "Grand i10 Nios", "i20", "i20 N Line", "Aura",
        "Exter", "Venue", "Venue N Line", "Verna",
        "Creta", "Creta N Line", "Alcazar",
        "Tucson", "Kona Electric", "Ioniq 5"
    ],
    "Tata Motors": [
        "Tiago", "Tiago EV", "Tigor", "Tigor EV",
        "Altroz", "Altroz Racer", "Punch", "Punch EV",
        "Nexon", "Nexon EV", "Curvv", "Curvv EV",
        "Harrier", "Safari"
    ],
    "Mahindra": [
        "XUV 3XO", "XUV400 EV", "XUV700",
        "Thar", "Thar Roxx", "Scorpio Classic", "Scorpio-N",
        "Bolero", "Bolero Neo", "Bolero Neo +",
        "Marazzo"
    ],
    "Toyota": [
        "Glanza", "Rumion", "Urban Cruiser Taisor",
        "Urban Cruiser Hyryder", "Innova Crysta",
        "Innova Hycross", "Fortuner", "Fortuner Legender",
        "Hilux", "Camry", "Vellfire", "Land Cruiser 300"
    ],
    "Kia": [
        "Sonet", "Seltos", "Carens", "Carnival",
        "EV6", "EV9"
    ],
    "Honda": [
        "Amaze", "City", "City e:HEV", "Elevate"
    ],
    "MG Motor": [
        "Comet EV", "Windsor EV", "Astor",
        "Hector", "Hector Plus", "ZS EV", "Gloster"
    ],
    "Volkswagen": [
        "Virtus", "Taigun", "Tiguan"
    ],
    "Skoda": [
        "Slavia", "Kushaq", "Superb", "Kodiaq", "Enyaq iV"
    ],
    "Renault": ["Kwid", "Triber", "Kiger"],
    "Nissan": ["Magnite", "X-Trail"],
    "Citroen": ["C3", "eC3", "C3 Aircross", "Basalt", "C5 Aircross"],
    "Jeep": ["Compass", "Meridian", "Wrangler", "Grand Cherokee"],
    "Force Motors": ["Gurkha", "Trax Cruiser", "Citiline"],
    "Isuzu": ["D-Max V-Cross", "MU-X", "Hi-Lander"],
    "BYD": ["Atto 3", "e6", "Seal"],
    "Mercedes-Benz": [
        "A-Class Limousine", "C-Class", "E-Class", "S-Class",
        "GLA", "GLB", "GLC", "GLC Coupe", "GLE", "GLS",
        "G-Class", "Maybach S-Class", "Maybach GLS",
        "EQA", "EQB", "EQE SUV", "EQS", "AMG GT", "AMG SL"
    ],
    "BMW": [
        "2 Series Gran Coupe", "3 Series Gran Limousine",
        "5 Series LWB", "6 Series GT", "7 Series",
        "X1", "X3", "X5", "X7", "XM", "Z4",
        "iX1", "i4", "iX", "i7", "M2", "M4", "M8"
    ],
    "Audi": [
        "A4", "A6", "A8 L", "Q3", "Q3 Sportback",
        "Q5", "Q7", "Q8", "Q8 e-tron",
        "e-tron GT", "RS5 Sportback", "RS e-tron GT"
    ],
    "Volvo": [
        "XC40 Recharge", "XC60", "XC90",
        "S90", "C40 Recharge", "EX30", "EX90"
    ],
    "Jaguar": ["F-Pace", "I-Pace", "F-Type"],
    "Land Rover": [
        "Range Rover", "Range Rover Sport", "Range Rover Velar",
        "Range Rover Evoque", "Discovery", "Discovery Sport",
        "Defender 90", "Defender 110", "Defender 130"
    ],
    "Porsche": [
        "Macan", "Macan EV", "Cayenne", "Cayenne Coupe",
        "Panamera", "Taycan", "718 Cayman", "718 Boxster",
        "911 Carrera", "911 GT3"
    ],
    "Lamborghini": ["Urus S", "Urus Performante", "Huracan Sterrato", "Huracan Tecnica", "Revuelto"],
    "Ferrari": ["Roma", "Roma Spider", "296 GTB", "296 GTS", "Purosangue", "SF90 Stradale"],
    "Aston Martin": ["Vantage", "DB12", "DBX", "DBX 707"],
    "Maserati": ["Ghibli", "Levante", "Quattroporte", "Grecale", "MC20", "GranTurismo"],
    "Rolls-Royce": ["Ghost", "Phantom", "Cullinan", "Spectre"],
    "Bentley": ["Continental GT", "Flying Spur", "Bentayga"],
    "Mini": ["Cooper 3-Door", "Cooper SE", "Countryman"],
    "Lexus": ["ES", "NX", "RX", "LX", "LM", "LS", "LC 500h"],
    "Tesla": ["Model 3", "Model Y", "Model S", "Model X"]
}


def seed_catalogs():
    """Insert brands and models if they don't already exist."""
    def insert_catalog(catalog: dict, vehicle_type: str):
        for brand_name, models in catalog.items():
            # Prefer to find a brand by name (avoid unique constraint violations).
            brand = CatalogBrand.query.filter_by(name=brand_name).first()
            if not brand:
                brand = CatalogBrand(name=brand_name, vehicle_type=vehicle_type)
                db.session.add(brand)
                db.session.flush()
            else:
                # If an existing brand has a different vehicle_type, keep the existing value
                # (we reuse the brand record and attach models to it). Log if available.
                try:
                    current_app.logger.debug(f"Reusing existing brand '{brand_name}' with vehicle_type={brand.vehicle_type}")
                except Exception:
                    pass

            # Insert models
            for model_name in models:
                exists = CatalogModel.query.filter_by(brand_id=brand.id, name=model_name).first()
                if not exists:
                    db.session.add(CatalogModel(brand_id=brand.id, name=model_name))

    insert_catalog(bike_catalog, 'bike')
    insert_catalog(car_catalog, 'car')
    db.session.commit()
