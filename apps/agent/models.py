"""
    The agent will run unstop after an order is placed. It communicates
    with the api using websockets and REACTS upon ticker receival with
    a callback.

    - The callback process is:

        1. check all stop-limit orders
            1.1. remove the expired ones, if any
            1.2. execute the valid one, if any
            * not allowed to have over three orders: 1 sell, 1 buy and 1 end (for each market)
                1.2.1. log the order
                1.2.2. signal db the state has changed and sets order to hold
                1.2.3. remove all stop-limit orders
                1.2.4. leave callback
        2. if none executed
            1. request data from database. If unchanged, database signals it.
            2. places new stop-limit order if current ORDER entry is not HOLD.
            3. sets VISUALIZED flag to True, avoiding replacing the order.

    The data requested by the database is as follows:
        1. order:
            - buy: ? -> 1
            - sell: ? -> -1
            - hold: ? -> ?
            - end: ? -> 0
            * where "?" is the current state
        2. stop_markup, limit_markup (%)
              stop = lowest_ask + stop_markup | highest_bid - stop_markup
              limit = lowest_ask + limit_markup | highest_bid - limit_markup
        3. amount
        4. expiration time
        5. market
        6. api (if more than one, each agent acts in parallel)
"""
