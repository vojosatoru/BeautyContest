# main.py
from ui_components import BeautyContestUI

if __name__ == "__main__":
    app = BeautyContestUI()
    if app.winfo_exists():
        app.mainloop()