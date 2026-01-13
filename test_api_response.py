#!/usr/bin/env python3
from app.database import get_db
from app.geocoding import get_city_coordinates

with get_db() as conn:
    conn.row_factory = None  # Get tuples instead of Row objects
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM workshops')
    total = c.fetchone()[0]
    
    c.execute('''
        SELECT id, city, location, date, time, style, difficulty, instructor_name, description
        FROM workshops
    ''')
    
    # Simulate what /workshops API returns
    workshops = []
    for row in c.fetchall():
        w_dict = {
            'id': row[0],
            'city': row[1],
            'location': row[2],
            'date': row[3],
            'time': row[4],
            'style': row[5],
            'difficulty': row[6],
            'instructor_name': row[7],
            'description': row[8],
            'lat': None,
            'lon': None
        }
        
        coords = get_city_coordinates(w_dict['city'])
        if coords:
            w_dict['lat'] = coords[0]
            w_dict['lon'] = coords[1]
        
        # Count participants
        c.execute("SELECT COUNT(*) FROM registrations WHERE workshop_id = ?", (w_dict['id'],))
        w_dict['participant_count'] = c.fetchone()[0]
        
        workshops.append(w_dict)
    
    print(f"Total workshops returned by API: {len(workshops)}")
    print(f"Workshops without coordinates: {sum(1 for w in workshops if w['lat'] is None)}")
    
    if workshops:
        print(f"\nFirst workshop:")
        print(workshops[0])

