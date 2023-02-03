from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def main_keyboard():
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.PRIMARY)

    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.PRIMARY)

    return keyboard.get_keyboard()
