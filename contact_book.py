"""
Contact Book
Store, view, search, update and delete contacts.
Contacts are saved to contacts.json so they persist between runs.
"""

import json
import re
from pathlib import Path

DATA_FILE = Path(__file__).with_name("contacts.json")
PHONE_RE = re.compile(r"^\+?[\d\s\-]{7,15}$")
EMAIL_RE = re.compile(r"^[\w.+\-]+@[\w\-]+(\.[\w\-]+)+$")


# ------------------------------------------------------------- data layer
class ContactBook:
    def __init__(self, path=DATA_FILE):
        self.path = path
        self.contacts = []   # list of dicts: name, phone, email, address
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.contacts = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.contacts = []

    def save(self):
        self.path.write_text(json.dumps(self.contacts, indent=2), encoding="utf-8")

    def sorted_contacts(self):
        return sorted(self.contacts, key=lambda c: c["name"].lower())

    def find_by_phone(self, phone):
        digits = re.sub(r"\D", "", phone)
        for c in self.contacts:
            if re.sub(r"\D", "", c["phone"]) == digits:
                return c
        return None

    def add(self, name, phone, email="", address=""):
        if self.find_by_phone(phone):
            raise ValueError("A contact with this phone number already exists")
        contact = {"name": name, "phone": phone, "email": email, "address": address}
        self.contacts.append(contact)
        self.save()
        return contact

    def search(self, query):
        q = query.lower().strip()
        q_digits = re.sub(r"\D", "", query)
        results = []
        for c in self.sorted_contacts():
            by_name = q in c["name"].lower()
            by_phone = bool(q_digits) and q_digits in re.sub(r"\D", "", c["phone"])
            if by_name or by_phone:
                results.append(c)
        return results

    def update(self, contact, **fields):
        for key, value in fields.items():
            if value is not None:
                contact[key] = value
        self.save()

    def delete(self, contact):
        self.contacts.remove(contact)
        self.save()


# ----------------------------------------------------------- input helpers
def ask(prompt, validator=None, error="Invalid input.", required=True, default=None):
    """Prompt until the input is valid. Blank keeps `default` when editing."""
    while True:
        value = input(prompt).strip()
        if not value:
            if default is not None:
                return default
            if not required:
                return ""
            print("  This field is required.")
            continue
        if validator and not validator(value):
            print(f"  {error}")
            continue
        return value


def valid_phone(v):
    return bool(PHONE_RE.match(v))


def valid_email(v):
    return bool(EMAIL_RE.match(v))


# --------------------------------------------------------------- display
def show_table(contacts):
    if not contacts:
        print("\n  (no contacts found)")
        return
    print(f"\n  {'#':<4}{'Name':<24}{'Phone':<18}")
    print("  " + "-" * 46)
    for i, c in enumerate(contacts, 1):
        print(f"  {i:<4}{c['name'][:22]:<24}{c['phone']:<18}")


def show_details(c):
    print("\n  ----------------------------------")
    print(f"  Name    : {c['name']}")
    print(f"  Phone   : {c['phone']}")
    print(f"  Email   : {c['email'] or '-'}")
    print(f"  Address : {c['address'] or '-'}")
    print("  ----------------------------------")


def pick_contact(book, action):
    """Search, then let the user choose one contact from the matches."""
    query = input(f"Enter name or phone of contact to {action}: ").strip()
    matches = book.search(query) if query else []
    if not matches:
        print("  No matching contact found.")
        return None
    if len(matches) == 1:
        show_details(matches[0])
        return matches[0]
    show_table(matches)
    while True:
        raw = input("Enter the # of the contact (or 0 to cancel): ").strip()
        if raw == "0":
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(matches):
            chosen = matches[int(raw) - 1]
            show_details(chosen)
            return chosen
        print("  Invalid number.")


# --------------------------------------------------------------- actions
def add_contact(book):
    print("\n-- Add new contact --")
    name = ask("Name: ")
    phone = ask("Phone: ", valid_phone, "Enter a valid phone number (7-15 digits).")
    email = ask("Email (optional): ", valid_email, "Enter a valid email address.",
                required=False)
    address = ask("Address (optional): ", required=False)
    try:
        book.add(name, phone, email, address)
        print(f"\n  Contact '{name}' added.")
    except ValueError as e:
        print(f"\n  Error: {e}")


def view_contacts(book):
    print("\n-- All contacts --")
    show_table(book.sorted_contacts())
    print(f"\n  Total: {len(book.contacts)}")


def search_contact(book):
    print("\n-- Search --")
    query = input("Enter name or phone number: ").strip()
    if not query:
        print("  Please enter something to search.")
        return
    results = book.search(query)
    show_table(results)
    if len(results) == 1:
        show_details(results[0])


def update_contact(book):
    print("\n-- Update contact --")
    contact = pick_contact(book, "update")
    if not contact:
        return
    print("\n  Press Enter to keep the current value.")
    name = ask(f"Name [{contact['name']}]: ", default=contact["name"])
    phone = ask(f"Phone [{contact['phone']}]: ", valid_phone,
                "Enter a valid phone number (7-15 digits).", default=contact["phone"])
    other = book.find_by_phone(phone)
    if other and other is not contact:
        print("  Error: another contact already uses this phone number.")
        return
    email = ask(f"Email [{contact['email'] or '-'}]: ", valid_email,
                "Enter a valid email address.", default=contact["email"])
    address = ask(f"Address [{contact['address'] or '-'}]: ", default=contact["address"])
    book.update(contact, name=name, phone=phone, email=email, address=address)
    print("\n  Contact updated.")


def delete_contact(book):
    print("\n-- Delete contact --")
    contact = pick_contact(book, "delete")
    if not contact:
        return
    if input(f"Delete '{contact['name']}'? (y/n): ").strip().lower() == "y":
        book.delete(contact)
        print("  Contact deleted.")
    else:
        print("  Cancelled.")


# ------------------------------------------------------------------ main
MENU = """
========== CONTACT BOOK ==========
  1. Add contact
  2. View all contacts
  3. Search contact
  4. Update contact
  5. Delete contact
  0. Exit
==================================
"""


def main():
    book = ContactBook()
    actions = {"1": add_contact, "2": view_contacts, "3": search_contact,
               "4": update_contact, "5": delete_contact}
    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action:
            action(book)
        else:
            print("  Invalid option. Please choose 0-5.")


if __name__ == "__main__":
    main()
