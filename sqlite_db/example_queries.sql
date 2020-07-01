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


SELECT 
    h1.*, 
    c.name 
FROM 
    hosts as h1 
    LEFT JOIN hostscomponents as h2 ON h1.hostname = h2.hostname 
    LEFT JOIN components as c ON c.componentID = h2.componentID;

SELECT 
    h1.hostname, 
    h1.ip, 
    h1.cpu, 
    COUNT(gpus.type) as num_gpus,
    COUNT(fpgas.type) as num_fpgas,
    h1.enabled 
FROM 
    hosts as h1 
    LEFT JOIN hostscomponents as h2 ON h1.hostname = h2.hostname 
    LEFT JOIN (SELECT * FROM components WHERE type = 1) as gpus ON gpus.componentID = h2.componentID
    LEFT JOIN (SELECT * FROM components WHERE type = 2) as fpgas ON fpgas.componentID = h2.componentID
GROUP BY h1.hostname;

-- ADDING is_free Column
SELECT 
    h1.hostname, 
    h1.ip, 
    h1.cpu, 
    COUNT(gpus.type) as num_gpus,
    COUNT(fpgas.type) as num_fpgas,
    h1.enabled,
    COUNT(frees.hostname) as is_free
FROM 
    hosts as h1 
    LEFT JOIN hostscomponents as h2 ON h1.hostname = h2.hostname 
    LEFT JOIN (SELECT * FROM components WHERE type = 1) as gpus ON gpus.componentID = h2.componentID
    LEFT JOIN (SELECT * FROM components WHERE type = 2) as fpgas ON fpgas.componentID = h2.componentID
    LEFT JOIN (
                SELECT hostname FROM hosts
                WHERE NOT EXISTS (
                SELECT host FROM reservations WHERE hosts.hostname = reservations.host)
                ) as frees ON h1.hostname = frees.hostname
GROUP BY h1.hostname
ORDER BY h1.hostname;


-- FIXED is_free
SELECT 
    h1.hostname, 
    h1.ip, 
    h1.cpu, 
    COUNT(gpus.type) as num_gpus,
    COUNT(fpgas.type) as num_fpgas,
    h1.enabled,
    frees.is_free as is_free
FROM 
    hosts as h1 
    LEFT JOIN hostscomponents as h2 ON h1.hostname = h2.hostname 
    LEFT JOIN (SELECT * FROM components WHERE type = 1) as gpus ON gpus.componentID = h2.componentID
    LEFT JOIN (SELECT * FROM components WHERE type = 2) as fpgas ON fpgas.componentID = h2.componentID
    LEFT JOIN ( 
                SELECT aux_frees1.hostname, COUNT(aux_frees2.hostname) as is_free
                FROM hosts as aux_frees1
                LEFT JOIN (
                    SELECT hostname FROM hosts
                    WHERE NOT EXISTS (
                    SELECT host FROM reservations WHERE hosts.hostname = reservations.host)
                    ) as aux_frees2 ON aux_frees1.hostname = aux_frees2.hostname
                GROUP BY aux_frees1.hostname
            ) as frees ON h1.hostname = frees.hostname
GROUP BY h1.hostname
ORDER BY h1.hostname;

CREATE VIEW hosts_complete AS 
SELECT 
    hosts.hostname,
    hosts.ip,
    hosts.cpu,
    count(sgpus.type) AS num_gpus,
    count(sfpgas.type) AS num_fpgas,
    hosts.enabled,
    s_frees.is_free AS is_free 
FROM 
    hosts 
    LEFT OUTER JOIN hostscomponents ON hosts.hostname = hostscomponents.hostname 
    LEFT OUTER JOIN (
                        SELECT 
                            components."componentID" AS "componentID",
                            components.name AS name,
                            components.type AS type 
                        FROM components 
                        WHERE components.type = 1
                    ) AS sgpus ON hostscomponents."componentID" = sgpus."componentID" 
    LEFT OUTER JOIN (
                        SELECT 
                            components."componentID" AS "componentID",
                            components.name AS name,
                            components.type AS type 
                        FROM components 
                        WHERE components.type = 2
                    ) AS sfpgas ON hostscomponents."componentID" = sfpgas."componentID" 
    LEFT OUTER JOIN (
                        SELECT 
                            hosts.hostname AS hostname,
                            count(aux_frees2.hostname) AS is_free 
                        FROM 
                            hosts,
                            (
                                SELECT 
                                    hosts.hostname AS hostname 
                                FROM hosts
                            ) AS aux_frees1 
                        LEFT OUTER JOIN (
                                            SELECT 
                                                hosts.hostname AS hostname 
                                            FROM hosts 
                                            WHERE NOT (EXISTS (
                                                                SELECT reservations.host 
                                                                FROM reservations 
                                                                WHERE reservations.host = hosts.hostname
                                                                )
                                                        )
                                        ) AS aux_frees2 ON aux_frees1.hostname = aux_frees2.hostname 
                        GROUP BY hosts.hostname
                    ) AS s_frees ON hosts.hostname = s_frees.hostname 
GROUP BY hosts.hostname

CREATE VIEW hosts_full AS 
SELECT 
    hosts.hostname,
    hosts.ip,
    scpus.name,
    count(sgpus.type) AS num_gpus,
    count(sfpgas.type) AS num_fpgas,
    hosts.enabled,
    s_frees.is_free AS is_free 
FROM 
    hosts 
    LEFT OUTER JOIN hostscomponents ON hosts.hostname = hostscomponents.hostname 
    LEFT OUTER JOIN (
                        SELECT 
                            components."componentID" AS "componentID",
                            components.name AS name,
                            components.type AS type 
                        FROM components 
                        WHERE components.type = 1
                    ) AS sgpus ON hostscomponents."componentID" = sgpus."componentID" 
    LEFT OUTER JOIN (
                        SELECT 
                            components."componentID" AS "componentID",
                            components.name AS name,
                            components.type AS type 
                        FROM components 
                        WHERE components.type = 2
                    ) AS sfpgas ON hostscomponents."componentID" = sfpgas."componentID" 
    LEFT OUTER JOIN (
                        SELECT 
                            aux_frees1.hostname AS hostname,
                            count(aux_frees2.hostname) AS is_free 
                        FROM (
                                SELECT 
                                    hosts.hostname AS hostname 
                                FROM 
                                    hosts
                            ) AS aux_frees1 
                        LEFT OUTER JOIN (
                                            SELECT 
                                                hosts.hostname AS hostname 
                                            FROM hosts 
                                            WHERE NOT (EXISTS (
                                                                SELECT 
                                                                    reservations.host 
                                                                FROM reservations 
                                                                WHERE reservations.host = hosts.hostname
                                                                )
                                                        )
                                        ) AS aux_frees2 ON aux_frees1.hostname = aux_frees2.hostname 
                        GROUP BY aux_frees1.hostname
                    ) AS s_frees ON hosts.hostname = s_frees.hostname 
    LEFT OUTER JOIN (
                        SELECT 
                            components."componentID" AS "componentID",
                            components.name AS name 
                        FROM components 
                        WHERE components.type = 0
                    ) AS scpus ON scpus."componentID" = hosts.cpu 
GROUP BY hosts.hostname