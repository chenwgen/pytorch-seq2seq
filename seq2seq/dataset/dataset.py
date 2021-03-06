import random
from seq2seq.dataset import Vocabulary, utils

class Dataset(object):
    """
    A class that encapsulates a dataset.

    Warning:
        Do not use this constructor directly, use one of the class methods to initialize.

    Note:
        Source or target sequences that are longer than the respective
        max length will be filtered.

    Args:
        src_max_len (int): maximum source sequence length
        tgt_max_len (int): maximum target sequence length
    """

    def __init__(self, src_max_len, tgt_max_len):
        # Prepare data
        self.src_max_len = src_max_len
        self.tgt_max_len = tgt_max_len

        # Declare vocabulary objects
        self.input_vocab = None
        self.output_vocab = None

        self.data = None


    @classmethod
    def from_file(cls, path, src_max_len, tgt_max_len, src_vocab=None, tgt_vocab=None, src_max_vocab=50000,
                 tgt_max_vocab=50000):
        """
        Initialize a dataset from the file at given path. The file
        must contains a list of TAB-separated pairs of sequences.

        Note:
            Source or target sequences that are longer than the respective
            max length will be filtered.
            As specified by maximum vocabulary size, source and target
            vocabularies will be sorted in descending token frequency and cutoff.
            Tokens that are in the dataset but not retained in the vocabulary
            will be dropped in the sequences.

        Args:
            path (str): path to the dataset file
            src_max_len (int): maximum source sequence length
            tgt_max_len (int): maximum target sequence length
            src_vocab (Vocabulary): pre-populated Vocabulary object or a path of a file containing words for the source language,
            default `None`. If a pre-populated Vocabulary object, `src_max_vocab` wouldn't be used.
            tgt_vocab (Vocabulary): pre-populated Vocabulary object or a path of a file containing words for the target language,
            default `None`. If a pre-populated Vocabulary object, `tgt_max_vocab` wouldn't be used.
            src_max_vocab (int): maximum source vocabulary size
            tgt_max_vocab (int): maximum target vocabulary size
        """
        obj = cls(src_max_len, tgt_max_len)
        pairs = utils.prepare_data(path, src_max_len, tgt_max_len)
        return cls._encode(obj, pairs, src_vocab, tgt_vocab, src_max_vocab, tgt_max_vocab)

    @classmethod
    def from_list(cls, src_data, tgt_data, src_max_len, tgt_max_len, src_vocab=None, tgt_vocab=None, src_max_vocab=50000,
                  tgt_max_vocab=50000):
        """
        Initialize a dataset from the source and target lists of sequences.

        Note:
            Source or target sequences that are longer than the respective
            max length will be filtered.
            As specified by maximum vocabulary size, source and target
            vocabularies will be sorted in descending token frequency and cutoff.
            Tokens that are in the dataset but not retained in the vocabulary
            will be dropped in the sequences.

        Args:
            src_data (list): list of source sequences
            tgt_data (list): list of target sequences
            src_max_len (int): maximum source sequence length
            tgt_max_len (int): maximum target sequence length
            src_vocab (Vocabulary): pre-populated Vocabulary object or a path of a file containing words for the source language,
            default `None`. If a pre-populated Vocabulary object, `src_max_vocab` wouldn't be used.
            tgt_vocab (Vocabulary): pre-populated Vocabulary object or a path of a file containing words for the target language,
            default `None`. If a pre-populated Vocabulary object, `tgt_max_vocab` wouldn't be used.
            src_max_vocab (int): maximum source vocabulary size
            tgt_max_vocab (int): maximum target vocabulary size
        """
        obj = cls(src_max_len, tgt_max_len)
        pairs = utils.prepare_data_from_list(src_data, tgt_data, src_max_len, tgt_max_len)
        return cls._encode(obj, pairs, src_vocab, tgt_vocab, src_max_vocab, tgt_max_vocab)

    def _encode(self, pairs, src_vocab=None, tgt_vocab=None, src_max_vocab=50000, tgt_max_vocab=50000):
        """
        Encodes the source and target lists of sequences using source and target vocabularies.

        Note:
            Source or target sequences that are longer than the respective
            max length will be filtered.
            As specified by maximum vocabulary size, source and target
            vocabularies will be sorted in descending token frequency and cutoff.
            Tokens that are in the dataset but not retained in the vocabulary
            will be dropped in the sequences.

        Args:
            pairs (list): list of tuples (source sequences, target sequence)
            src_vocab (Vocabulary): pre-populated Vocabulary object or a path of a file containing words for the source language,
            default `None`. If a pre-populated Vocabulary object, `src_max_vocab` wouldn't be used.
            tgt_vocab (Vocabulary): pre-populated Vocabulary object or a path of a file containing words for the target language,
            default `None`. If a pre-populated Vocabulary object, `tgt_max_vocab` wouldn't be used.
            src_max_vocab (int): maximum source vocabulary size
            tgt_max_vocab (int): maximum target vocabulary size
        """
        # Read in vocabularies
        self.input_vocab = self._init_vocab(zip(*pairs)[0], src_max_vocab, src_vocab)
        self.output_vocab = self._init_vocab(zip(*pairs)[1], tgt_max_vocab, tgt_vocab)

        # Translate input sequences to token ids
        self.data = []
        for pair in pairs:
            src = self.input_vocab.indices_from_sequence(pair[0])
            dst = self.output_vocab.indices_from_sequence(pair[1])
            self.data.append((src, dst))
        return self

    def _init_vocab(self, sequences, max_num_vocab, vocab):
        resp_vocab = Vocabulary(max_num_vocab)
        if vocab is None:
            for sequence in sequences:
                resp_vocab.add_sequence(sequence)
            resp_vocab.trim()
        elif isinstance(vocab, Vocabulary):
            resp_vocab = vocab
        elif isinstance(vocab, str):
            for tok in utils.read_vocabulary(vocab, max_num_vocab):
                resp_vocab.add_token(tok)
        else:
            raise AttributeError('{} is not a valid instance on a vocabulary. None, instance of Vocabulary class \
                                 and str are only supported formats for the vocabulary'.format(vocab))
        return resp_vocab

    def __len__(self):
        return len(self.data)

    def num_batches(self, batch_size):
        """
        Get the number of batches given batch size.

        Args:
            batch_size(int): number of examples in a batch

        Returns:
            int: number of batches
        """
        return len(range(0, len(self.data), batch_size))

    def make_batches(self, batch_size):
        """
        Create a generator that generates batches in batch_size over data.

        Args:
            batch_size (int): number of pairs in a mini-batch

        Yields:
            (list(str), list(str)): next pair of source and target variable in a batch

        """
        if len(self.data) < batch_size:
            raise OverflowError("batch size = {} cannot be larger than data size = {}".
                                format(batch_size, len(self.data)))
        for i in range(0, len(self.data), batch_size):
            cur_batch = self.data[i:i + batch_size]
            source_variables = [pair[0] for pair in cur_batch]
            target_variables = [pair[1] for pair in cur_batch]

            yield (source_variables, target_variables)

    def shuffle(self, seed=None):
        """
        Shuffle the data.

        Args:
            seed(int): provide a value for the random seed; default seed=None is truly random
        """
        if seed is not None:
            random.seed(seed)
        random.shuffle(self.data)
