SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS=0;

INSERT INTO `roles` (`id`, `name`, `description`) VALUES (1, 'admin', 'администратор');

INSERT INTO `roles` (`id`, `name`, `description`) VALUES (2, 'moderator', 'модератор');

INSERT INTO `roles` (`id`, `name`, `description`) VALUES (3, 'user', 'пользователь');

INSERT INTO `genres` (`id`, `name`) VALUES (1, 'Роман');

INSERT INTO `genres` (`id`, `name`) VALUES (2, 'Фантастика');

INSERT INTO `genres` (`id`, `name`) VALUES (3, 'Детектив');

INSERT INTO `genres` (`id`, `name`) VALUES (4, 'Научная литература');

INSERT INTO `genres` (`id`, `name`) VALUES (5, 'История');

INSERT INTO `genres` (`id`, `name`) VALUES (6, 'Учебная литература');

INSERT INTO `users` (`id`, `login`, `password_hash`, `last_name`, `first_name`, `middle_name`, `role_id`) VALUES (1, 'admin', 'scrypt:32768:8:1$qk5MiQbl8lxWtRb2$b4d6ddeadff00150f85b639c7b1b84797a690db7ae56fd0519f63aa525b97214fb65206d698330b28f98a61d9e75772e261456a307ad8224c7b8cd641a807477', 'Администратор', 'Системы', '', 1);

SET FOREIGN_KEY_CHECKS=1;
