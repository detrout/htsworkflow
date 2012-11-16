from argparse import ArgumentParser
import logging
from htsworkflow.util import rdfhelp, rdfinfer

def main(cmdline=None):
    parser = make_parser()
    args = parser.parse_args(cmdline)

    logging.basicConfig(level=logging.INFO)

    validate_urls(args.urls)

def make_parser():
    parser = ArgumentParser()
    parser.add_argument('urls',nargs='*')
    return parser

def validate_urls(urls):
    model = rdfhelp.get_model()
    rdfhelp.add_default_schemas(model)

    for u in urls:
        rdfhelp.load_into_model(model, None, u)

    engine = rdfinfer.Infer(model)
    #engine.think()
    engine.validate()

if __name__ == "__main__":
    main()
