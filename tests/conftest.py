"""
This file is part of Track Shape Utils.

Copyright (C) 2025 Peter Grønbæk Andersen <peter@grnbk.io>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import pytest


@pytest.fixture(scope="session")
def global_storage():
    data = {
        "doesnotexist_path": "./tests/data/doesnotexist.dat",
        "global_tsection_extension_path": "./tests/data/global_tsection_extension.dat",
        "local_tsection_path": "./tests/data/local_tsection.dat"
    }
    return data