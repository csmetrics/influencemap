# Influencemap Project @ ANU

Influence in the academic communities has been an area of interest for researchers. This can be seen in the popularity of applications like google scholar and the various metrics created for ranking papers, authors, conferences, etc.

We aim to provide a visualization tool which allows users to easily search and visualize the flow of academic influence. Our visualization maps influence in the form of an influence flower.

![alt text](https://github.com/csmetrics/influencemap/blob/master/assets/img/example_flower_1.png)

The node in the center of the flower denotes the ego entity, the entitiy in which we are looking at influence with respect to. The leaf nodes are the most influential (look below for definition of our influence) entities with respect to the ego.

Each of the edges of the graph signifies the flow of influence to and from the ego node, the strenth of this relation is reflected in the thickness of the edge. The red edges denotes the influence the ego has towards the outer entities (an outer entity citing a paper by the ego). The blue edges denotes the influence the outer entities have towards the ego (the ego cites a paper by one of the outer entities).

![Alt text](https://github.com/csmetrics/influencemap/blob/master/assets/img/influence_flow.svg)

The hue of the outer nodes signify the ratio of influence in and out. A blue node indicates that the associated entity has influence the ego more than the ego has influenced itself. Likewise, a red node indicates the ego has influenced the node's entity more than it has influenced the ego.

We define two entities to be coauthors if the entities have contributed to the same paper. Coauthor of the ego are signified by nodes with green borders and greyed out names.

## methodology
To quantify academic influence, we define influence as a function of paper
citations. The scoring of influence is done with respect to entities
(author, institute, journal, or conference) and how entities cite other
entities. To visualise influence we use influence flowers. An influence
flower aims to show a dense representation of the influence in which an
entity (the center node, denoted as the ego) has with several other entities.

### calculating the influence one entity has on another entity

#### removing self-citations

We define a self-citation between papers and a cited paper as a relation
dependent on the ego. A paper citation is a self-citation if both papers
have the ego as an author.

#### Why not remove all coauthor papers instead?
 
When removing all coauthor papers (all scores from papers with a coauthor of
the referencing paper authors) we found the 'cut down' to be too extreme. This
would greatly effect the produced flower, leaving one with little to no
information.

#### weighting the citations

[TBD]

#### Normalisation

Influence on an entity is calculated as the sum of the per author weight for each of the citations to a paper written by that entity, as shown below.

![calculation of a's influence on b](https://github.com/csmetrics/influencemap/blob/master/assets/influence_calulation.png)

For example, consider the following four paper database.

| Name         | Paper            | no. authors | cites papers                     |
|--------------|------------------|-------------|----------------------------------|
| John Smith   | Algorithms       | 2           | [Linear Algebra]                 |
| John Smith   | Machine Learning | 3           | [Linear Algebra, Computation]    |
| Maria Garcia | Linear Algebra   | 2           | None                             |
| Maria Garcia | Computation      | 4           | [Algorithms]                     |

In this case John's influence on Maria is 0.5 (John's paper Algorithm's has a weight of 0.5 and was cited once by Maria). 

On the other hand Maria's influence on John is 1.25 (Linear Algebra has a weight of 0.5 and it was cited twice by John, Computation has a weight of 0.25 and was cited once by John).

#### page-rank style weighting of papers

[TODO] generate sample graphics using different weighting schemes

### one database containing all useful tables

[TBD]

### how data is cached

[TBD]

### visualising the influence
To visualise the influence that one entity has on others, the influence scores are calculated as described above for the entity and each other entity that cites it. The scores of the most influential entities are normalised and used as weights for the graph's edges to show their relative influence. Similarly, visualising how one is influenced involves finding the scores for each entity that has influenced (been cited by) them and plotting the normalised scores as weights on a weighted graph.
