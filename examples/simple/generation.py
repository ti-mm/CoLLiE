import sys
sys.path.append("/mnt/lustre/zhangshuo/projects/collie/")
from collie.models.llama.model import LlamaModel, LlamaArguments
from collie.trainer.trainer import Trainer
from collie.metrics.decode import DecodeMetric

from transformers import LlamaTokenizer
from transformers.generation.utils import GenerationConfig
from torch.utils.data import Dataset
import torch

tokenizer = LlamaTokenizer.from_pretrained("/mnt/lustre/zhangshuo/model/llama-7b-hf", 
                                           padding_side="left")
tokenizer.pad_token_id = 0
tokenizer.bos_token_id = 1
tokenizer.eos_token_id = 2

args = LlamaArguments.from_pretrained("/mnt/lustre/zhangshuo/model/llama-7b-hf")
args.dp_size = 2
args.pp_size = 2
args.tp_size = 2
args.eval_batch_size = 4
args.ds_config = {
    "fp16": {"enabled": True}
}

class GenerationDataset(Dataset):
    def __init__(self, sentences = []) -> None:
        super().__init__()
        self.sentences = sentences
        
    def __len__(self):
        return len(self.sentences)
    
    def __getitem__(self, index):
        return self.sentences[index]
    
def collate_fn(batch):
    input_ids = tokenizer(batch, 
                          return_tensors="pt", 
                          padding=True)["input_ids"]
    return input_ids, input_ids
dataset = GenerationDataset([
    "It's a beautiful day to",
    "This is my favorite",
    "As we discussed yesterday",
    "I'm going to",
    "As well known to all",
    "A",
    "So this is the reason why",
    "We have to"
])
torch.set_default_tensor_type(torch.HalfTensor)
model = LlamaModel.from_pretrained("/mnt/lustre/zhangshuo/model/test/", args=args)

trainer = Trainer(model=model,
                  train_dataset=dataset,
                  eval_dataset=dataset,
                  eval_config=GenerationConfig(max_new_tokens=100),
                  metrics=[DecodeMetric(tokenizer=tokenizer, gather_result=True, only_rank0_update=True)],
                  eval_dataset_collate_fn=collate_fn,
                  train_dataset_collate_fn=collate_fn,
                  args=args)
torch.cuda.empty_cache()
trainer.eval()