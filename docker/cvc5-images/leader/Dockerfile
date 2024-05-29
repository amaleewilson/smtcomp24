################### Use cvc5
FROM cloud-cvc5:common AS builder
USER root

RUN chmod -R 1777 /tmp

################### Extract cvc5 in run stage
FROM satcomp-infrastructure:leader AS cvc5_liaison
WORKDIR /

ENV PATH="/usr/local/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"

RUN /usr/bin/python3.8 -m pip install mpi4py
COPY --from=builder /cvc5/build/bin/cvc5 cvc5
COPY --from=builder /cvc5/build/bin/cvc5 /competition/cvc5
COPY --from=builder /scrambler/scrambler /competition/scrambler

COPY --chown=ecs-user /run-script-smtcomp-current /competition/
COPY --chown=ecs-user /init_solver.sh /competition/
COPY --chown=ecs-user /run_solver.sh /competition/
COPY --chown=ecs-user ./do_solving.py /competition/
COPY --chown=ecs-user ./solver_utils.py /competition/
COPY --chown=ecs-user /solver /competition/
COPY --chown=ecs-user /cleanup /competition/
USER ecs-user
RUN chmod +x /competition/run-script-smtcomp-current
RUN chmod +x /competition/init_solver.sh
RUN chmod +x /competition/run_solver.sh
RUN chmod +x /competition/do_solving.py
RUN chmod +x /competition/solver_utils.py
RUN chmod +x /competition/solver
RUN chmod +x /competition/cleanup