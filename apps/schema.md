# Application Schema

## Agent explanation
    
The agent will run unstop after an order is placed. It communicates
with the api using websockets and REACTS upon ticker receival with 
a callback.

The callback process is:
        
        1. check all stop-limit orders
            1.1. remove the expired ones, if any
            1.2. execute the valid one, if any
            * not allowed to have over three orders: 1 sell, 1 buy and 1 end (for each market, user, exchange)
                1.2.1. log the order
                1.2.2. signal db the state has changed and sets order to hold
                1.2.3. remove all stop-limit orders (for each market, user, exchange)
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
        
## Scholar explanation

The scholar will run periodically after a new Investment entry is placed.
It communicates with the api using http.

A new Investment needs:

        1. api
        2. market
        3. amount
        4. mstop_markup, limit_markup (%)
        5. stop_limit_expiration_time
        6. strategy_expiration_time:
            the time the BEST strategy shall hold before it is reevaluated.
        7. analysis_period: schedules the analysis process
        8. candlestick_period
        9. start_date
        10. strategies: list of strategies to be tested
        11. strategies configuration:
            1. hyperparameters

The analysis process finds the best strategy with the best parameters. Then,
it creates a new order entry in the broker/database for the {api, market} 
combination:

        1. ORDER: buy, sell, hold, end
        2. VISUALIZED: False
        3. STRATEGY
        4. PARAMETERS

Periodically, the `api.market.chart` is retrieved and the strategy updates the order entry

Beyond that, every analysis result should be LOGGED and recorded in a database
for further analysis.

## Database models

1. user
    - e-mail
    - password
    - full name
2. exchange
    - connection lib
    - markets
    - other configs
3. exchange connection
    - user (fk)
    - exchange (fk)
    - public key
    - secret key
4. strategy
    - strategy lib/id
    - configurations (nosql)
5. strategy config
    - strategy id
    - params
6. investment
    - exchange (fk)
    - market (validation - exchange)
    - amount (validation - balance)
    - markup
    - stop_limit_expiration_time
    - strategy_expiration_time
    - analysis_period
    - candlestick_period
    - start_date
    - strategies (many-to-many)
    - strategies configurations (matrix)
7. order (redis)
    - investment_id
    - order type
    - best_strategy
    - best_params
    