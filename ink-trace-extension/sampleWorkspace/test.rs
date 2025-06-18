#![cfg_attr(not(feature = "std"), no_std, no_main)]

#[ink::contract]
pub mod flipper {

    #[ink(storage)]
    pub struct Flipper {
        value: bool,
    }

    impl Flipper {
        /// Конструктор для створення контракту Flipper.
        /// Ініціалізує `value` початковим значенням.
        #[ink(constructor)]
        pub fn new(init_value: bool) -> Self {
            // <-- БРЕЙКПОІНТ 1: Поставте тут, щоб перевірити зупинку на вході в конструктор.
            let instance = Self {
                value: init_value,
            };
            // <-- БРЕЙКПОІНТ 2: Поставте тут, щоб перевірити крок після ініціалізації.
            instance
        }

        /// Просто перевертає значення `value` з true на false або навпаки.
        #[ink(message)]
        pub fn flip(&mut self) {
            // <-- БРЕЙКПОІНТ 3: Поставте тут, щоб перевірити зупинку перед зміною стану.
            self.value = !self.value;
            // <-- БРЕЙКПОІНТ 4: Поставте тут, щоб побачити стан після зміни.
        }

        /// Просто повертає поточне значення `value`.
        #[ink(message)]
        pub fn get(&self) -> bool {
            // <-- БРЕЙКПОІНТ 5: Поставте тут, щоб перевірити зупинку при читанні стану.
            self.value
        }
    }
}