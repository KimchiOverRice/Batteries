#!/usr/bin/env python

import asyncio
import click
import logging
import inquirer
import time
import os
import sys

from elcon import ElconTcCharger

charger = ElconTcCharger()

LOG = logging.getLogger(__name__)

def loglevel_choice():
    return click.Choice([logging.getLevelName(name) for name in
                      [logging.CRITICAL,
                       logging.ERROR,
                       logging.WARNING,
                       logging.INFO,
                       logging.DEBUG]])

@click.command()
@click.option(
    "--loglevel",
    type=loglevel_choice(),
    prompt=False,
    default=logging.getLevelName(logging.INFO)
)

def cli(loglevel) -> None:
    click.echo('=== Otherlab ===')

    logging.basicConfig()
    LOG.setLevel(loglevel)

    event_loop = asyncio.get_event_loop()

    event_loop.create_task(charger.run())
    event_loop.create_task(menu())

    event_loop.run_forever()


async def menu():
    LOG.info("CAN tester.")

    while True:
        selection = inquirer.list_input('Main menu',
                                        choices=['Loop',
                                                 'Message1',
                                                 'Message2',
                                                 'Quit'])


        if selection == 'Loop':
            current_params = ElconTcCharger.Message1()
            while True:
                charger.send(current_params)
                await asyncio.sleep(1.0)
        elif selection == 'Message1':
            msg1 = ElconTcCharger.Message1()
            msg1.max_charging_voltage = float(inquirer.text('Max charging voltage', default='0'))
            msg1.max_charging_current = float(inquirer.text('Max charging current', default='0'))
            msg1.battery_protection_enabled = bool(inquirer.text('Battery protection enabled', default='0'))
            charger.send(msg1)
        elif selection == 'Message2':
            msg2 = ElconTcCharger.Message2()
            msg2.output_voltage = float(inquirer.text('Output voltage', default='0'))
            msg2.output_current = float(inquirer.text('Max charging current', default='0'))
            keys = ElconTcCharger.Message2.status_flags_keys()
            for key in keys:
                msg2.status_flags[key] = int(inquirer.text(f'Status flag {key}', default='0'))
            charger.send(msg2)
        else:
            LOG.info('Goodbye')
            sys.exit(0)
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    cli(auto_envvar_prefix='OTHERLAB')