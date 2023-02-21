## Hydrogen Plant Mixed Integer Linear Optimser 

This Mixed Integer Linear Programming Model (MILP) has been developed as part of an Ofgem SIF funded Alpha Phase project to design and build a 'Gas System of the Future', Digital Twin in collaboration with SGN, Esri, AWS and DNV. SIF funds ambitious, innovative projects which can help shape the future of the energy networks and accelerate the transition to net zero, at lowest cost to consumers to help transform the UK into the ‘Silicon Valley’ of energy, making it the best place to be an energy consumer and energy entrepreneur. Facilitating knowledge transfer is one of the key principles of the SIF. Ultimately, consumers are funding Projects and we want the learning generated to be disseminated as effectively as possible to ensure that all licensees, and therefore all consumers, can benefit from Projects. The MILP has been released under the MIT licence to share learnings through providing referenable code.

### Epic & User Story

The user story related to Alex - a Hydrogen Production Manager - who is responsible for managing hydrogen production. The volume of production is not a straightforward decision for Alex whose role is to minimise the cost of production and to produce hydrogen using green energy wherever possible. To achieve this, he must consider factors such as the Wind Generation Energy Forecast and the Hydrogen Demand Forecast - both which are directly influenced by the weather - to decide how much hydrogen to produce. He must also consider the Grid Electricity Pricing, since he may need to purchase electricity for hydrogen production if there is insufficient energy available from wind.

A Mixed Integer Programming (MIP) problem with a cost function of electrical power and renewable power was determined to be a suitable approach with some assumptions made about the linearity of variables. The model was coded in python using an open source solver, Pulp. Given a forecast of the hydrogen demand, wind power and associated costs, the model calculates how much hydrogen Alex should produce from each power source to minimise cost within a range of physical and policy  constraints. Those constraints for example include minimum and maximum storage limit, and minimum and maximum rate of production. Each time Alex runs the model, he will be provided with a production plan based on the most recent forecast.

### Links

<ol>
  <li>Ofgem Strategic Innovation Fund: [https://www.ofgem.gov.uk/strategic-innovation-fund-sif](https://www.ofgem.gov.uk/strategic-innovation-fund-sif)</li>
</ol>
