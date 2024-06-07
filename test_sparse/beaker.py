from moduler.decorator import example


class Beaker:
    """
    A beaker is a container that can hold a certain volume of liquid.
    This class is used to represent the beaker in the virtual lab.
    """

    def __init__(self, max_volume: float):
        """
        Create a beaker with a maximum volume.
        :param max_volume: The maximum volume of the beaker.
        """
        self.max_volume = max_volume
        self.contents = []
        self.temperature = 25.0  # Assuming room temperature in Celsius

    """
    ## Operations of beaker
    """

    def add_liquid(self, liquid_type: str, volume: float) -> bool:
        """
        :param liquid_type: The type of liquid, e.g. water, ethanol, etc.
        :param volume: The volume of the liquid added.
        :return: whether the liquid was successfully added.
        """
        if self.current_volume() + volume > self.max_volume:
            return False
        self.contents.append((liquid_type, volume))
        return True

    def add_solid(self, solid_type: str, weight: float) -> bool:
        """
        :param solid_type: The type of solid, e.g. salt, sugar, etc.
        :param weight: The weight of the solid added.
        :return: whether the solid was successfully added.
        """
        self.contents.append((solid_type, weight))
        return True

    """
    ## Status of beaker
    """

    def current_volume(self) -> float:
        """
        :return: The current volume of the beaker.
        """
        return sum([c[1] for c in self.contents])

    def remove_liquid(self, volume: float) -> bool:
        """
        Attempt to remove a specified volume of liquid, returns True if successful.
        This method does not specify from which liquid the volume is removed.
        """
        if volume > self.current_volume():
            return False
        # Simply reduce the volume of the last added liquid for simplicity
        for i in range(len(self.contents) - 1, -1, -1):
            if self.contents[i][1] == 'liquid':
                _, material, current_volume = self.contents[i]
                new_volume = current_volume - volume
                if new_volume <= 0:
                    volume -= current_volume
                    del self.contents[i]
                else:
                    self.contents[i] = (material, 'liquid', new_volume)
                    volume = 0
                if volume <= 0:
                    break
        return True

    def mix_contents(self):
        """
        Simulate mixing the contents of the beaker. This is a placeholder operation.
        """
        print("Contents mixed.")

    def heat(self, temperature_increase: float):
        """
        Increase the temperature of the beaker's contents by a specified amount.
        """
        self.temperature += temperature_increase

    def cool(self, temperature_decrease: float):
        """
        Decrease the temperature of the beaker's contents by a specified amount.
        """
        self.temperature -= temperature_decrease

    def measure_ph(self) -> float:
        """
        Return the pH level of the contents. This is a placeholder operation that always returns 7.0.
        """
        return 7.0  # Assume neutral pH for simplification

    def filter_solids(self):
        """
        Filter out solids from the beaker, leaving only liquids. This operation is always successful.
        """
        self.contents = [item for item in self.contents if item[1] == 'liquid']

    def evaporate_liquid(self, volume: float) -> bool:
        """
        Attempt to evaporate a specified volume of liquid, returns True if successful.
        This simplistically reduces the volume of the liquid.
        """
        return self.remove_liquid(volume)

    def dissolve_solid(self):
        """
        If possible, dissolve solid contents into liquid. This is a placeholder operation.
        """
        print("Solids dissolved into the liquid.")

    def separate_liquids(self):
        """
        Attempt to separate different types of liquids into distinct layers. This is a placeholder operation.
        """
        print("Liquids separated into distinct layers.")

    def transfer_liquid(self, volume: float, target_beaker: 'Beaker') -> bool:
        """
        Attempt to transfer a specified volume of liquid to another beaker.
        """
        if self.remove_liquid(volume):
            return target_beaker.add_liquid('transferred liquid', volume)
        return False

    def calculate_density(self) -> float:
        """
        Return the density of the beaker's contents based on the types and volumes of materials.
        This is a placeholder operation that assumes a uniform density.
        """
        return 1.0  # Assume the density of water for simplification

    def is_full(self) -> bool:
        """
        Returns True if the beaker is at maximum capacity.
        """
        return self.current_volume() >= self.max_volume

    def is_empty(self) -> bool:
        """
        Returns True if the beaker has no contents.
        """
        return not self.contents

    def list_contents(self) -> list:
        """
        Returns a list of all contents in the beaker.
        """
        return self.contents

    def has_liquid(self, liquid_type: str) -> bool:
        """
        Returns True if the beaker contains a specified type of liquid.
        """
        return any(material == liquid_type for material, state, _ in self.contents if state == 'liquid')

    def has_solid(self, solid_type: str) -> bool:
        """
        Returns True if the beaker contains a specified type of solid.
        """
        return any(material == solid_type for material, state, _ in self.contents if state == 'solid')

    def total_weight(self) -> float:
        """
        Calculates and returns the total weight of the beaker's contents.
        This is a placeholder operation, assuming the weight is equal to the volume.
        """
        return sum(volume for _, _, volume in self.contents)

    def clear_contents(self):
        """
        Removes all contents from the beaker.
        """
        self.contents.clear()

    def print_content_details(self):
        """
        Prints a detailed description of all contents, including type and quantity.
        """
        for material, state, amount in self.contents:
            print(f"{state.capitalize()} of {material}: {amount} units")

    def calculate_volume_of_liquid(self, liquid_type: str) -> float:
        """
        Calculates and returns the volume of a specified type of liquid in the beaker.
        """
        return sum(volume for material, state, volume in self.contents if state == 'liquid' and material == liquid_type)


class Desk:
    """
    A desk is for holding beakers. It can hold multiple beakers.
    """

    def __init__(self):
        self.beakers = []


@example
def put_beaker_on_desk(desk: Desk, beaker: Beaker):
    """
    Here is an example of putting a beaker on a desk.
    """
    desk.beakers.append(beaker)
    return desk
