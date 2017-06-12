############################################################################################
## File Name: circles.py
## Description: Python 2 adaptation of a genetic algorithm that finds the largest possible
##              circle that can be placed amongst a group of circles without overlapping.
##
##              The original algorithm, written in C++, can be found here:
##              http://www.ai-junkie.com/ga/intro/gat3.html
############################################################################################

import pygame, random

##########################
## CONSTANTS
##########################

WIDTH = 400             # screen dimensions
HEIGHT = 400

WHITE = (255, 255, 255) # colours
BLACK = (0, 0, 0)
RED = (255, 0, 0)

NUM_CIRCLES = 20        # number of circle obstacles
POPULATION_SIZE = 150   # number of chromosomes in each generation
CHROMOSOME_SIZE = 30    # length in bits of each chromosome

NUM_ELITES = 4          # number of elite chromosomes taken from each generation
NUM_COPIES = 1          # number of copies of the elites taken

CROSSOVER_CHANCE = 0.8  # chance to crossover two chromosomes
MUTATION_CHANCE = 0.05  # chance to flip an individual bit

##########################
## CLASSES
##########################

class Chromosome(object):
    '''Object consisting of a string of bits and an associated fitness score.'''
    def __init__(self, bits = None):
        if bits is None:                                    # if no starting value is provided,
            bits = int(random.getrandbits(CHROMOSOME_SIZE)) # randomly generate a string of bits
        self.bits = bits    # initialize the bits
        self.fitness = 0    # initial fitness score is 0

    def decode(self):
        '''Resolve a chromosome into x, y, and r values.'''
        x = get_bits(self.bits, 20, 30)
        y = get_bits(self.bits, 10, 20)
        r = get_bits(self.bits, 0, 10)

        return x, y, r

    def update_fitness(self, circles):
        '''Update the fitness score based on the positions of circles on the screen.'''
        decoded = self.decode()
        if out_of_bounds(decoded) or overlap_any(decoded, circles): # fitness is 0 if the circle goes off the screen
            self.fitness = 0                                        # or overlaps any other circle
        else:
            self.fitness = decoded[2] # otherwise, fitness is the radius of the circle

    def crossover(self, other):
        '''Swap the head of this chromosome with the tail of another and return the resultant two chromosomes'''
        if random.random() < CROSSOVER_CHANCE:                                              # roll for whether the crossover will occur or not
            pos = random.randrange(1, CHROMOSOME_SIZE)                                      # choose a random position at which to split the chromosomes
            crossed1 = concatenate_bits(self.bits >> pos, clear_end(other.bits, pos), pos)  # add the head of self to the tail of other
            crossed2 = concatenate_bits(other.bits >> pos, clear_end(self.bits, pos), pos)  # add the head of other to the tail of self
            return Chromosome(crossed1), Chromosome(crossed2)                               # return the resultant chromosomes
        else:
            return Chromosome(self.bits), Chromosome(other.bits) # create new chromosome objects to avoid altering the original chromosomes

    def mutate(self):
        '''Iterate through the bits of a chromosome, and flip certain bits according to a percent chance.'''
        for i in xrange(CHROMOSOME_SIZE):
            if random.random() < MUTATION_CHANCE:
                self.bits = self.bits ^ (1 << i) # flip the bit using XOR

class Population(object):
    '''Object consisting of a list of Chromosomes.'''
    def __init__(self):
        self.chromosomes = [Chromosome() for i in xrange(POPULATION_SIZE)] # randomly generate a number of chromosomes during initialization
        self.total_fitness = 0 # initial sum of all fitnesses is 0
        self.best = self.chromosomes[0]

    def update_fitnesses(self, circles):
        '''Update the fitnesses of each chromosome, and total the results.'''
        self.total_fitness = 0                          # reset the fitnesses sum before updating
        for chromosome in self.chromosomes:             
            chromosome.update_fitness(circles)
            self.total_fitness += chromosome.fitness    
            if chromosome.fitness >= self.best.fitness: # keep note of the best chromosome
                self.best = chromosome

    def choose_chromosome(self):
        '''Randomly choose a chromosome according to a probability proportional to its fitness score.'''
        threshold = self.total_fitness * random.random()    # sum at which a chromosome will be chosen
        total = 0                                           # running total of chromosome fitnesses
        for chromosome in self.chromosomes:
            total += chromosome.fitness     # add each chromosome's fitness to the total
            if total > threshold:           # until the threshold is reached
                return chromosome           # at which point the chromosome is chosen
        return chromosome                   # return the last chromosome in case the threshold is not reached (which should never happen)

    def get_elites(self):
        '''Get NUM_COPIES of the top NUM_ELITES chromosomes.'''
        sorted_chromosomes = sorted(self.chromosomes, key = lambda chromosome: chromosome.fitness)  # sort chromosomes by fitness score
        elites = sorted_chromosomes[-NUM_ELITES:]                                                   # choose top NUM_ELITES chromosomes
        return [Chromosome(elite.bits) for elite in elites for i in xrange(NUM_COPIES)]             # return NUM_COPIES of the elites

    def get_best(self):
        '''Return the chromosome with the top fitness score.'''
        return self.best

    def run_generation(self, circles):
        '''Create the next generation of chromosomes.'''
        self.update_fitnesses(circles)                      # update all fitness scores
        next_gen = self.get_elites()                        # initialize the next generation with the elites of the previous

        while len(next_gen) < POPULATION_SIZE:              # until the next generation is filled
            choice1 = self.choose_chromosome()              # randomly choose two chromosomes
            choice2 = self.choose_chromosome()              # according to their fitness score

            choice1, choice2 = choice1.crossover(choice2)   # cross them over
            choice1.mutate()                                # mutate them
            choice2.mutate()

            next_gen.extend([choice1, choice2])             # and add them to the next generation
            
        self.chromosomes = next_gen                         # update the list of chromosomes

##########################
## FUNCTIONS
##########################
        
def clear_end(bits, new_end):
    '''Set all bits after a certain slice to 0.

    >>> bits = int('0b1010101', 2)
    >>> bin(clear_end(bits, 3))
    '0b101'
    '''
    mask = (1 << new_end) - 1 # creates a string of 1's of length (new_end)
    return bits & mask        # bitwise AND sets all bits after that string to 0

def get_bits(bits, start, stop):
    '''Return the bits between two slices of a binary string

    >>> bits = int('0b1110111', 2)
    >>> bin(get_bits(bits, 2, 6))
    '0b1101'
    '''
    return clear_end(bits, stop) >> start # remove the bits after the stop slice and before the start slice
                                            

def concatenate_bits(left, right, right_length):
    '''Add the bits of a binary string to those of another.

    >>> left = int('0b10101', 2)
    >>> right = int('0b1111', 2)
    >>> bin(concatenate_bits(left, right, 4))
    '0b101011111'
    >>> bin(concatenate_bits(left, right, 8))
    '0b1010100001111'
    '''
    return (left << right_length) | right # bit shift left the correct number of spaces, then set the bits of the right using bitwise OR

def overlapping(circle1, circle2):
    '''Check if a circle overlaps another circle'''
    x1, y1, r1 = circle1 # unpack the circle tuples
    x2, y2, r2 = circle2
    d = (x2-x1)**2 + (y2-y1)**2 # get the square of the distance between the circle's centres using pythagorean theorem
    
    if d < (r1+r2)**2:  # if the distance is less than the sum of the radii, they overlap
        return True
    else:
        return False

def overlap_any(circle, circles):
    '''Check if a circle overlaps any circle in a list of circles.'''
    for i in xrange(len(circles)):
        if overlapping(circle, circles[i]):
            return True
    return False

def out_of_bounds(circle):
    '''Check if any portion of a circle is beyond the boundaries of the screen.'''
    x, y, r = circle
    return (x-r < 0) or (y-r < 0) or (x+r > WIDTH) or (y+r > HEIGHT)

def generate_circle(minR, maxR):
    '''Randomly generate a circle within the boundaries of the screen.'''
    r = random.randint(minR, maxR)
    x = random.randint(r, WIDTH - r)
    y = random.randint(r, HEIGHT - r)

    return x,y,r

def populate_circles(n):
    '''Create a list of random, non-overlapping circles.'''
    circles = []
    while len(circles) < n:
        new_circle = generate_circle(10,30)
        if not overlap_any(new_circle, circles):
            circles.append(new_circle)
    return circles

def reset():
    circles = populate_circles(NUM_CIRCLES)
    population = Population()
    generation_num = 0
    return circles, population, generation_num

def render_text():
    generation_str = 'Generation: ' + str(generation_num)
    reset_str = 'R - Reset'
    pause_str = 'P - Pause/Play'
    strings = [generation_str, reset_str, pause_str]
    rendered = [font.render(string, 1, BLACK) for string in strings]
    return rendered

def draw_text(rendered):
    screen.blit(rendered[0], (5, 0))
    screen.blit(rendered[1], (5, HEIGHT-15))
    screen.blit(rendered[2], (WIDTH//2, HEIGHT-15))
        
def redraw_screen():
    screen.fill(WHITE)
    for x, y, r in circles:
        pygame.draw.circle(screen, BLACK, (x,y), r, 1)

    best_solution = population.get_best()   # draw the best solution in the population
    x, y, r = best_solution.decode()
    pygame.draw.circle(screen, RED, (x,y), r)
    try:
        pygame.draw.circle(screen, BLACK, (x,y), r, 1) # if r == 0, would raise a ValueError
    except ValueError:
        pass

    draw_text(render_text())
    pygame.display.update()

##########################
## MAIN PROGRAM
##########################

circles, population, generation_num = reset()

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
font = pygame.font.SysFont('Courier New', 15)

running = True
paused = False
while running:
    redraw_screen()
    
    if not paused:
        population.run_generation(circles)
        generation_num += 1
        
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_r:
                circles, population, generation_num = reset()
            if event.key == pygame.K_p:
                paused = not paused
                
pygame.quit()
