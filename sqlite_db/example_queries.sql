--LIST NUMBER OF RESERVATIONS PER HOST
SELECT
    hosts.hostname,
    COUNT(res.host_id) as num_reservations
FROM
    hosts
    LEFT JOIN reservations as res ON hosts.id = res.host_id
GROUP BY hosts.id
ORDER BY hosts.hostname;

--LIST FREE HOSTS
SELECT
    hosts.hostname,
    COUNT(res.host_id) as num_reservations
FROM
    hosts
    LEFT JOIN reservations as res ON hosts.id = res.host_id
GROUP BY hosts.id
HAVING num_reservations = 0
ORDER BY hosts.hostname;

--LIST CURRENT RESERVATIONS
SELECT
    hosts.hostname,
    users.username,
    res.reservation_type,
    res.begin_date,
    res.end_date
FROM
    reservations as res
    LEFT JOIN hosts ON hosts.id = res.host_id
    LEFT JOIN users ON users.id = res.user_id
ORDER BY 1,2;

