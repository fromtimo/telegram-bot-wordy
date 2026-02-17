from aiogram.fsm.state import State, StatesGroup

class FSMMainMenu(StatesGroup):
    main_menu = State()

class FSMLearnWords(StatesGroup):
    deck_selection = State()
    show_new_words = State()
    testing = State()
    show_problem_words = State()
    testing_problem_words = State()

class FSMSettings(StatesGroup):
    settings_menu = State()
    notifications = State()
    delete_confirmation = State()