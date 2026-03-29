"""Seed the people table using Wikipedia API for verified image URLs.

Usage: uv run python scripts/seed_people_wiki.py
"""
import sys
import os
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import supabase

PEOPLE = [
    ("Dwayne Johnson", ["The Rock"], "actor"),
    ("Leonardo DiCaprio", ["Leo"], "actor"),
    ("Beyoncé", ["Queen Bey"], "musician"),
    ("Taylor Swift", [], "musician"),
    ("Cristiano Ronaldo", ["CR7"], "athlete"),
    ("Lionel Messi", ["Leo Messi"], "athlete"),
    ("Tom Hanks", [], "actor"),
    ("Oprah Winfrey", [], "other"),
    ("Elon Musk", [], "other"),
    ("Adele", [], "musician"),
    ("Brad Pitt", [], "actor"),
    ("Angelina Jolie", [], "actor"),
    ("Morgan Freeman", [], "actor"),
    ("Will Smith", ["The Fresh Prince"], "actor"),
    ("Jennifer Lawrence", [], "actor"),
    ("Robert Downey Jr.", ["RDJ"], "actor"),
    ("Scarlett Johansson", [], "actor"),
    ("Tom Cruise", [], "actor"),
    ("Meryl Streep", [], "actor"),
    ("Denzel Washington", [], "actor"),
    ("Rihanna", ["RiRi"], "musician"),
    ("Drake (musician)", ["Drake", "Drizzy"], "musician"),
    ("Ed Sheeran", [], "musician"),
    ("Bruno Mars", [], "musician"),
    ("Lady Gaga", ["Stefani Germanotta"], "musician"),
    ("Justin Bieber", [], "musician"),
    ("Eminem", ["Slim Shady", "Marshall Mathers"], "musician"),
    ("Kanye West", ["Ye"], "musician"),
    ("LeBron James", ["King James"], "athlete"),
    ("Serena Williams", [], "athlete"),
    ("Usain Bolt", [], "athlete"),
    ("Roger Federer", [], "athlete"),
    ("Michael Jordan", ["MJ"], "athlete"),
    ("Neymar", ["Neymar Jr"], "athlete"),
    ("Stephen Curry", ["Steph Curry"], "athlete"),
    ("Tiger Woods", [], "athlete"),
    ("Barack Obama", [], "politician"),
    ("Keanu Reeves", [], "actor"),
    ("Chris Hemsworth", [], "actor"),
    ("Gal Gadot", [], "actor"),
    ("Ryan Reynolds", [], "actor"),
    ("Margot Robbie", [], "actor"),
    ("Chris Evans (actor)", ["Chris Evans"], "actor"),
    ("Zendaya", [], "actor"),
    ("Billie Eilish", [], "musician"),
    ("Ariana Grande", [], "musician"),
    ("Selena Gomez", [], "musician"),
    ("Katy Perry", [], "musician"),
    ("The Weeknd", ["Abel Tesfaye"], "musician"),
    ("Dua Lipa", [], "musician"),
    ("Jeff Bezos", [], "other"),
    ("Mark Zuckerberg", ["Zuck"], "other"),
    ("Bill Gates", [], "other"),
    ("Albert Einstein", [], "other"),
    ("Marilyn Monroe", [], "actor"),
    ("Muhammad Ali", ["Cassius Clay"], "athlete"),
    ("Michael Jackson", ["King of Pop"], "musician"),
    ("Elvis Presley", ["The King"], "musician"),
    ("Madonna (entertainer)", ["Madonna", "Queen of Pop"], "musician"),
    ("David Bowie", ["Ziggy Stardust"], "musician"),
    ("Freddie Mercury", [], "musician"),
    ("Prince (musician)", ["Prince", "The Artist"], "musician"),
    ("Shakira", [], "musician"),
    ("Jennifer Lopez", ["JLo"], "musician"),
    ("Tom Brady", ["TB12"], "athlete"),
    ("Kobe Bryant", ["Black Mamba"], "athlete"),
    ("David Beckham", ["Becks"], "athlete"),
    ("Lewis Hamilton", [], "athlete"),
    ("Rafael Nadal", ["Rafa"], "athlete"),
    ("Novak Djokovic", ["Nole"], "athlete"),
    ("Mike Tyson", ["Iron Mike"], "athlete"),
    ("Arnold Schwarzenegger", ["The Terminator"], "actor"),
    ("Sylvester Stallone", ["Sly"], "actor"),
    ("Harrison Ford", [], "actor"),
    ("Samuel L. Jackson", [], "actor"),
    ("Al Pacino", [], "actor"),
    ("Robert De Niro", [], "actor"),
    ("Johnny Depp", [], "actor"),
    ("Nicole Kidman", [], "actor"),
    ("Julia Roberts", [], "actor"),
    ("Anne Hathaway", [], "actor"),
    ("Natalie Portman", [], "actor"),
    ("Emma Watson", [], "actor"),
    ("Emma Stone", [], "actor"),
    ("Chris Pratt", [], "actor"),
    ("Jason Momoa", [], "actor"),
    ("Vin Diesel", [], "actor"),
    ("Miley Cyrus", [], "musician"),
    ("Harry Styles", [], "musician"),
    ("Nicki Minaj", [], "musician"),
    ("Jay-Z", ["Shawn Carter", "Hov"], "musician"),
    ("Snoop Dogg", ["Snoop Lion"], "musician"),
    ("Kendrick Lamar", ["K-Dot"], "musician"),
    ("Bob Marley", [], "musician"),
    ("John Lennon", [], "musician"),
    ("Paul McCartney", ["Macca"], "musician"),
    ("Elton John", [], "musician"),
    ("Stevie Wonder", [], "musician"),
    ("Pelé", ["Edson Arantes"], "athlete"),
    ("Diego Maradona", [], "athlete"),
    ("Simone Biles", [], "athlete"),
    ("Conor McGregor", ["The Notorious"], "athlete"),
    ("Floyd Mayweather Jr.", ["Money", "Floyd Mayweather"], "athlete"),
    ("Timothée Chalamet", [], "actor"),
    ("Pedro Pascal", [], "actor"),
    ("Cillian Murphy", [], "actor"),
    ("Sydney Sweeney", [], "actor"),
    ("Jenna Ortega", [], "actor"),
    ("Ana de Armas", [], "actor"),
    ("Jackie Chan", [], "actor"),
    ("Jim Carrey", [], "actor"),
    ("Adam Sandler", [], "actor"),
    ("Kevin Hart", [], "actor"),
    ("Olivia Rodrigo", [], "musician"),
    ("Bad Bunny", ["Benito"], "musician"),
    ("Travis Kelce", [], "athlete"),
    ("Patrick Mahomes", [], "athlete"),
    ("Giannis Antetokounmpo", ["Greek Freak"], "athlete"),
    ("Kylian Mbappé", ["Kylian Mbappe"], "athlete"),
    ("Max Verstappen", [], "athlete"),
    ("Kim Kardashian", [], "other"),
    ("Gordon Ramsay", [], "other"),
    ("Nelson Mandela", ["Madiba"], "politician"),
    ("Queen Elizabeth II", [], "politician"),
    ("Pope Francis", [], "other"),
    ("Audrey Hepburn", [], "actor"),
    ("Charlie Chaplin", ["The Tramp"], "actor"),
    ("Bruce Lee", [], "actor"),
    ("Clint Eastwood", [], "actor"),
    ("Robin Williams", [], "actor"),
    ("Eddie Murphy", [], "actor"),
    ("Cate Blanchett", [], "actor"),
    ("Viola Davis", [], "actor"),
    ("Joaquin Phoenix", [], "actor"),
    ("Matt Damon", [], "actor"),
    ("George Clooney", [], "actor"),
    ("Benedict Cumberbatch", [], "actor"),
    ("Hugh Jackman", [], "actor"),
    ("Idris Elba", [], "actor"),
    ("Charlize Theron", [], "actor"),
    ("Kate Winslet", [], "actor"),
    ("Millie Bobby Brown", [], "actor"),
    ("Lil Wayne", ["Weezy"], "musician"),
    ("Pharrell Williams", [], "musician"),
    ("John Legend", [], "musician"),
    ("Alicia Keys", [], "musician"),
    ("Zlatan Ibrahimović", ["Zlatan", "Ibra"], "athlete"),
    ("Michael Phelps", [], "athlete"),
    ("Venus Williams", [], "athlete"),
    ("Kevin Durant", ["KD"], "athlete"),
    ("Mohamed Salah", ["Mo Salah"], "athlete"),
    ("Robert Lewandowski", ["Lewy"], "athlete"),
    ("Virat Kohli", [], "athlete"),
    ("Sandra Bullock", [], "actor"),
    ("Reese Witherspoon", [], "actor"),
    ("Ryan Gosling", [], "actor"),
    ("Daniel Craig", [], "actor"),
    ("Christian Bale", [], "actor"),
    ("Mark Wahlberg", [], "actor"),
    ("Seth Rogen", [], "actor"),
    ("Jonah Hill", [], "actor"),
    ("Zac Efron", [], "actor"),
    ("Chris Rock", [], "actor"),
    ("Dave Chappelle", [], "actor"),
    ("Whoopi Goldberg", [], "actor"),
    ("Halle Berry", [], "actor"),
    ("Doja Cat", [], "musician"),
    ("Lana Del Rey", ["Elizabeth Grant"], "musician"),
    ("J. Cole", ["Jermaine Cole"], "musician"),
    ("Lizzo", [], "musician"),
    ("Post Malone", ["Austin Post"], "musician"),
    ("Travis Scott", ["La Flame"], "musician"),
    ("Cardi B", [], "musician"),
    ("SZA (singer)", ["SZA", "Solána Rowe"], "musician"),
    ("Sam Smith", [], "musician"),
    ("Sia (musician)", ["Sia"], "musician"),
    ("Erling Haaland", [], "athlete"),
    ("Luka Dončić", ["Luka Doncic"], "athlete"),
    ("Naomi Osaka", [], "athlete"),
    ("Sachin Tendulkar", [], "athlete"),
    ("Marie Curie", [], "other"),
    ("Frida Kahlo", [], "other"),
    ("Stephen Hawking", [], "other"),
    ("Greta Thunberg", [], "other"),
    ("Malala Yousafzai", [], "other"),
    ("David Attenborough", [], "other"),
    ("Jane Fonda", [], "actor"),
    ("Sean Penn", [], "actor"),
    ("Liam Neeson", [], "actor"),
    ("Russell Crowe", [], "actor"),
    ("Javier Bardem", [], "actor"),
    ("Penélope Cruz", ["Penelope Cruz"], "actor"),
    ("Antonio Banderas", [], "actor"),
    ("Salma Hayek", [], "actor"),
    ("Will Ferrell", [], "actor"),
    ("Ben Stiller", [], "actor"),
    ("Tina Fey", [], "actor"),
    ("Amy Poehler", [], "actor"),
    ("Steve Carell", [], "actor"),
    ("Jason Statham", [], "actor"),
    ("Megan Fox", [], "actor"),
    ("Gwen Stefani", [], "musician"),
    ("Christina Aguilera", [], "musician"),
    ("Usher (musician)", ["Usher"], "musician"),
    ("Justin Timberlake", [], "musician"),
    ("Britney Spears", [], "musician"),
    ("Whitney Houston", [], "musician"),
    ("Mariah Carey", [], "musician"),
    ("Céline Dion", ["Celine Dion"], "musician"),
    ("Frank Sinatra", [], "musician"),
    ("Jimi Hendrix", [], "musician"),
]

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary"

def get_image_url(wiki_title: str) -> str | None:
    """Fetch thumbnail URL from Wikipedia REST API."""
    url = f"{WIKI_API}/{wiki_title.replace(' ', '_')}"
    try:
        resp = requests.get(url, headers={"User-Agent": "WhoIsIt-Game/1.0"})
        if resp.status_code != 200:
            return None
        data = resp.json()
        thumb = data.get("thumbnail", {}).get("source")
        if thumb:
            # Get a larger version (600px)
            thumb = thumb.rsplit("/", 1)[0] + "/600px-" + thumb.rsplit("/", 1)[1].split("px-", 1)[1]
        return thumb
    except Exception:
        return None

def main():
    people_data = []
    failed = []

    for i, (wiki_name, aliases, category) in enumerate(PEOPLE):
        # Display name: strip disambiguation like "(musician)"
        display_name = wiki_name.split(" (")[0]

        print(f"[{i+1}/{len(PEOPLE)}] Fetching {display_name}...", end=" ")
        image_url = get_image_url(wiki_name)

        if not image_url:
            print("SKIP (no image)")
            failed.append(display_name)
            continue

        # Add display name as alias if wiki name differs
        all_aliases = list(aliases)
        if display_name != wiki_name and display_name not in all_aliases:
            all_aliases.append(display_name)

        people_data.append({
            "name": display_name,
            "aliases": all_aliases,
            "image_url": image_url,
            "category": category,
            "license": "CC-BY-SA",
            "attribution_url": f"https://en.wikipedia.org/wiki/{wiki_name.replace(' ', '_')}",
        })
        print(f"OK")

        # Rate limit: Wikipedia asks for <200 req/s
        if i % 50 == 49:
            time.sleep(1)

    print(f"\nFound {len(people_data)} people with images, {len(failed)} failed")

    if failed:
        print(f"Failed: {', '.join(failed[:20])}")

    # Clear existing and insert fresh
    print("Clearing existing people...")
    # Delete in reverse dependency order
    supabase.table("daily_challenges").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("people").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    print("Inserting new people...")
    for i in range(0, len(people_data), 50):
        batch = people_data[i:i+50]
        supabase.table("people").insert(batch).execute()
        print(f"  Batch {i//50 + 1} ({len(batch)} people)")

    print("Done!")

if __name__ == "__main__":
    main()
