################### Use cvc5
# this is just so you cna copy things
FROM cloud-cvc5:common AS builder
USER root

################### Extract cvc5 in run stage
# this is the actual base image 
FROM satcomp-infrastructure:worker AS cvc5_liaison
WORKDIR /

RUN /usr/bin/python3.8 -m pip install mpi4py

COPY --from=builder /cvc5/build/bin/cvc5 cvc5
COPY --from=builder /cvc5/build/bin/cvc5 /competition/cvc5
COPY --from=cloud-cvc5:leader /competition/do_solving.py /competition/
COPY --from=cloud-cvc5:leader /competition/solver_utils.py /competition/
COPY --from=cloud-cvc5:leader /competition/run-script-smtcomp-current /competition/

RUN chown ecs-user /competition/do_solving.py 
RUN chown ecs-user /competition/solver_utils.py
COPY --chown=ecs-user /worker /competition
COPY --chown=ecs-user /init_solver.sh /competition
COPY --chown=ecs-user /cleanup /competition

USER ecs-user
RUN chmod +x /competition/cleanup
RUN chmod +x /competition/worker
RUN chmod +x /competition/do_solving.py
RUN chmod +x /competition/solver_utils.py
